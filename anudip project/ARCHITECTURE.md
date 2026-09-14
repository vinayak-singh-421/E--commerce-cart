# Architecture Document
## E-commerce Cart & Order System

**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-09-14

---

## 1. Architectural Goals

- Clear separation between **runtime data structures** (Linked List, Graph) and **durable storage** (relational DB / cache).
- Modular services so Cart, Order, and Recommendation logic can evolve or scale independently.
- Stateless API layer; all session/cart state externalized to Redis/DB so any server instance can serve any request.

## 2. High-Level System Diagram (textual)

```
                        +-------------------+
                        |      Client        |
                        |  (Web / React SPA) |
                        +----------+---------+
                                   |
                                   v
                        +-------------------+
                        |    API Gateway /   |
                        |   REST/GraphQL     |
                        +---+-----+-----+----+
                            |     |     |
              +-------------+   |     +--------------+
              v                 v                    v
     +----------------+ +----------------+  +----------------------+
     |  Cart Service   | | Order Service   |  | Recommendation Svc  |
     | (Linked List)   | | (Order History) |  | (Graph traversal)   |
     +--------+--------+ +--------+--------+  +----------+-----------+
              |                   |                       |
              v                   v                       v
     +----------------+ +----------------+  +----------------------+
     |  Redis (active  | | PostgreSQL     |  | Graph Store          |
     |  cart cache)    | | (orders,       |  | (in-memory adjacency |
     |                 | |  order_items)  |  |  list, rebuilt from  |
     |                 | |                |  |  Postgres nightly)  |
     +----------------+ +----------------+  +----------------------+
              |
              v
     +----------------+
     | PostgreSQL      |
     | (cart_items,    |
     |  durable backup)|
     +----------------+

     +-----------------------------------------------------+
     |            Batch Job: Graph Builder (nightly)         |
     |  reads order_items -> computes co-purchase edges ->   |
     |  writes product_edges table -> reloads Graph Store    |
     +-----------------------------------------------------+
```

## 3. Component Breakdown

### 3.1 Cart Service
- Owns the **Doubly Linked List** implementation per active user session.
- Reads/writes through to Redis for fast session persistence; Postgres `cart_items` as durable fallback (e.g., cart recovery after cache eviction).
- Exposes: add, remove, update quantity, reorder, get cart, clear cart.

### 3.2 Order Service
- Converts a Cart (linked list) into an immutable Order snapshot on checkout.
- Owns `orders` and `order_items` tables.
- Exposes: checkout, list orders (paginated, recency-ordered), get order detail, reorder (rehydrates cart from an order).

### 3.3 Recommendation Service
- Owns the **Graph** (adjacency list) representation of product relationships.
- Graph lives in-memory (or in a graph-friendly cache like Redis with sorted sets per node) for low-latency neighbor lookups; rebuilt periodically by the batch job from durable `product_edges` table.
- Exposes: recommend(context: cart | order | product, ids[]) → ranked product list.

### 3.4 Graph Builder (Batch Job)
- Offline/scheduled job (e.g., nightly cron or event-driven after order volume threshold).
- Scans `order_items` to compute co-purchase weights, merges with catalog-derived `SAME_CATEGORY` edges, writes to `product_edges`.
- Triggers Recommendation Service to reload its in-memory graph.

## 4. Data Flow: Key Scenarios

**Add to Cart**
Client → API Gateway → Cart Service → mutate in-memory Linked List → write-through to Redis (+ async persist to Postgres) → response with updated cart summary.

**Checkout**
Client → API Gateway → Order Service → request current cart from Cart Service → traverse Linked List → build immutable Order → persist to Postgres → instruct Cart Service to clear cart → response with order confirmation.

**Get Recommendations**
Client → API Gateway → Recommendation Service → identify seed product IDs (from cart or order context) → traverse Graph adjacency lists → rank & dedupe → response with top-N products.

## 5. Deployment View

- **API layer:** stateless, horizontally scalable (multiple instances behind a load balancer).
- **Redis:** single managed cluster for active cart cache (with persistence/AOF enabled to avoid cart loss on restart).
- **PostgreSQL:** primary durable store, read replicas for order history queries at scale.
- **Recommendation graph:** loaded per service instance at boot and refreshed on a schedule; for very large catalogs, consider a dedicated graph store (e.g., Redis Graph or Neo4j) instead of in-process memory.

## 6. Scalability Considerations

| Concern | Mitigation |
|---|---|
| Hot products with very high graph degree | Cap neighbor list size per node; pre-sort top-K at build time |
| Large concurrent cart writes | Redis handles high write throughput; Postgres write is async/batched |
| Order history growth | Paginate; index on `(user_id, created_at)` |
| Graph staleness | Nightly rebuild acceptable for v1; move to incremental updates in v2 |

## 7. Security & Isolation

- All Cart/Order endpoints require authenticated session; cart/order data is scoped by `userId`.
- Rate limiting on cart mutation endpoints to prevent abuse.
- Recommendation queries are read-only and do not expose other users' cart/order data.

## 8. Future Architecture Considerations (see Roadmap)

- Move recommendation graph to a dedicated graph database for advanced traversal (multi-hop, weighted shortest path) at scale.
- Event-driven graph updates (real-time edge weight increments on each checkout) instead of nightly batch.
- Cart service sharding by user hash if Redis becomes a bottleneck.
