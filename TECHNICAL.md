# Technical Design Document
## E-commerce Cart & Order System

**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-09-14

---

## 1. Purpose

This document specifies the technical implementation of the Cart, Order History, and Recommendation modules, with a focus on the data structures used (Linked List, Graph) and how they map to system behavior.

## 2. Tech Stack (Suggested)

| Layer | Technology |
|---|---|
| Backend | Node.js / Express (or Python / FastAPI) |
| Database | PostgreSQL (orders, products) + Redis (active cart cache) |
| In-memory structures | Custom Linked List (Cart), Custom Graph (Recommendations) |
| Frontend | React |
| API | REST (or GraphQL) |
| Testing | Jest / Pytest |

> Stack is illustrative; swap per team preference. The data-structure design below is language-agnostic.

## 3. Core Data Structures

### 3.1 Cart — Doubly Linked List

**Why a linked list?**
- Cart items are frequently added/removed, and order within the cart matters (recently added items, manual reordering).
- A doubly linked list gives O(1) insertion/removal when you already hold a reference to the node (e.g., "remove this line item"), and O(1) traversal in both directions for reordering UI (move up/down).
- Avoids the O(n) shifting cost of array splice operations for middle-of-list removals.

**Node structure:**
```
CartItemNode {
  productId: string
  quantity: int
  unitPrice: decimal
  addedAt: timestamp
  prev: CartItemNode | null
  next: CartItemNode | null
}
```

**Cart structure:**
```
Cart {
  userId: string
  head: CartItemNode | null
  tail: CartItemNode | null
  size: int
  nodeIndex: Map<productId, CartItemNode>   // O(1) lookup by product
}
```

> `nodeIndex` is a supporting hash map so we don't need O(n) traversal to find a product's node before removing/updating it. This is a common, accepted pairing (linked list + hash index) — it does not defeat the purpose of the linked list, which is to preserve *order* and give O(1) structural mutation once located.

**Core operations:**

| Operation | Complexity | Notes |
|---|---|---|
| addItem(productId, qty) | O(1) | Append to tail; if exists, update qty via nodeIndex |
| removeItem(productId) | O(1) | Locate via nodeIndex, unlink node |
| updateQuantity(productId, qty) | O(1) | Locate via nodeIndex, mutate field |
| moveItem(productId, direction) | O(1) | Swap adjacent node pointers |
| traverseCart() | O(n) | For rendering / checkout summary |
| clearCart() | O(1) | Drop head/tail/index refs (GC handles nodes) |

**Persistence strategy:**
- Active cart lives in Redis as a serialized linked list (or reconstructed from a Postgres `cart_items` table ordered by a `position` column) for durability across sessions.
- In-memory linked list is the *runtime* representation during an active session; DB/Redis is the *durable* representation.

### 3.2 Order History — Append-Only Structure

- Orders are immutable once created, so a simple **singly linked list ordered by timestamp (most recent → oldest)**, or a database table indexed by `userId + createdAt`, both work. In-memory, a singly linked list is sufficient since we never remove or reorder nodes, only prepend new ones and traverse.

```
OrderNode {
  orderId: string
  items: OrderItem[]     // snapshot copy, not live cart nodes
  status: enum
  createdAt: timestamp
  next: OrderNode | null  // points to the next-older order
}
```

- On checkout: traverse the Cart linked list once (O(n)) to build an immutable `OrderItem[]` snapshot, prepend a new `OrderNode` to the user's order history, then clear the cart.

### 3.3 Recommendations — Graph

**Why a graph?**
- Product relationships are naturally graph-shaped: "bought together," "same category," "viewed after." A graph lets us model multiple relationship types and traverse them to find relevant neighbors.

**Graph structure (adjacency list — basic graph, undirected or weighted-directed depending on relationship):**
```
ProductGraph {
  adjacency: Map<productId, List<Edge>>
}

Edge {
  to: productId
  weight: float        // e.g., co-purchase frequency
  type: enum            // BOUGHT_TOGETHER | SAME_CATEGORY | VIEWED_TOGETHER
}
```

**Core operations:**

| Operation | Complexity | Notes |
|---|---|---|
| addEdge(a, b, weight, type) | O(1) | Push into both adjacency lists (undirected) |
| getNeighbors(productId, limit) | O(k log k) | k = degree of node; sort by weight, take top-N |
| recommendForCart(cart) | O(m·k log k) | m = distinct products in cart, union top neighbors, dedupe, rank |
| recommendForOrderHistory(orders) | O(m·k log k) | Same, seeded from purchased products |

**Recommendation algorithm (v1, heuristic — not ML):**
1. For each product in the cart (or last N orders), fetch its top-K neighbors by edge weight.
2. Merge candidate lists, summing weights for products that appear from multiple source items.
3. Exclude products already in the cart / already purchased (configurable).
4. Sort merged candidates by aggregate weight, descending.
5. Return top 4–10.

**Graph population:**
- Seeded via a batch job over historical order data: every pair of products co-purchased in the same order gets a `BOUGHT_TOGETHER` edge, weight incremented per occurrence.
- `SAME_CATEGORY` edges derived from catalog metadata.
- Graph is rebuilt/updated on a schedule (e.g., nightly), not real-time, in v1.

## 4. API Design (REST, illustrative)

```
POST   /api/cart/items              { productId, quantity }
DELETE /api/cart/items/:productId
PATCH  /api/cart/items/:productId   { quantity }
PATCH  /api/cart/items/:productId/move   { direction: "up" | "down" }
GET    /api/cart

POST   /api/orders/checkout         (converts current cart -> order)
GET    /api/orders                  (list, paginated, most recent first)
GET    /api/orders/:orderId
POST   /api/orders/:orderId/reorder

GET    /api/recommendations?context=cart
GET    /api/recommendations?context=order&orderId=xyz
```

## 5. Data Model (Relational, for durable storage)

```
users(id, name, email, ...)

cart_items(id, user_id, product_id, quantity, unit_price, position, added_at)

orders(id, user_id, status, created_at, total)

order_items(id, order_id, product_id, quantity, unit_price)

products(id, name, category, price, ...)

product_edges(product_id_a, product_id_b, weight, type)
```

`cart_items.position` maintains linked-list order for reconstruction after reads from Postgres/Redis.

## 6. Error Handling

- Adding an out-of-stock item → reject with `409 Conflict`, return alternative recommendations.
- Removing a non-existent cart item → `404 Not Found`.
- Concurrent cart mutation (multi-tab) → last-write-wins with optimistic version check (`cart.version` field).

## 7. Testing Strategy

- **Unit tests:** Linked list operations (add/remove/move/traverse) in isolation with edge cases (empty cart, single item, head/tail removal).
- **Unit tests:** Graph operations (addEdge, getNeighbors, ranking/merge logic).
- **Integration tests:** Full checkout flow (cart → order → history).
- **Load tests:** Recommendation endpoint under high-degree graph nodes (popular products).

## 8. Complexity Summary

| Feature | Structure | Key Benefit |
|---|---|---|
| Cart | Doubly Linked List + Hash Index | O(1) mutation, preserves order |
| Order History | Singly Linked List / append-only log | O(1) prepend, natural recency order |
| Recommendations | Adjacency-list Graph | Models multi-type relationships, efficient neighbor lookup |
