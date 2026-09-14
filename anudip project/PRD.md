# Product Requirements Document (PRD)
## E-commerce Cart & Order System

**Version:** 1.0
**Status:** Draft
**Owner:** Product/Engineering Team
**Last Updated:** 2026-09-14

---

## 1. Overview

The E-commerce Cart & Order System is a core module of an online shopping platform. It allows users to manage a shopping cart, view their order history, and receive product recommendations based on their browsing/purchase behavior.

This project is also a demonstration of applying core data structures to real-world problems:
- **Linked List** → Shopping Cart (ordered, frequently mutated collection of items)
- **Basic Graph** → Recommendation Engine (product-to-product relationships)

## 2. Problem Statement

Users need a fast, reliable way to:
1. Add, remove, and reorder items in a cart before checkout.
2. Review past orders for reordering, tracking, or returns.
3. Discover relevant products based on what they've bought or viewed, increasing engagement and average order value.

Existing simplistic array-based cart implementations struggle with frequent insertions/removals in the middle of a list and don't naturally model relationships between products for recommendations.

## 3. Goals & Objectives

| Goal | Success Metric |
|---|---|
| Fast cart mutations | O(1) add/remove at known node reference |
| Reliable order history | 100% of completed orders retrievable, sorted by date |
| Relevant recommendations | ≥15% click-through on recommended items |
| Maintainable codebase | Modular design, documented data structures |

## 4. Non-Goals

- Payment gateway integration (out of scope for v1; stubbed only)
- Multi-currency support
- Advanced ML-based personalization (v1 uses graph traversal heuristics, not ML models)
- Mobile native apps (web-first)

## 5. User Personas

- **Shopper (Primary):** Browses products, adds to cart, checks out, revisits order history.
- **Returning Customer:** Wants quick reorder of past purchases and relevant suggestions.
- **Admin (Secondary):** Manages product catalog and views order data (read-only in v1).

## 6. Functional Requirements

### 6.1 Shopping Cart
- FR-1: User can add a product to the cart.
- FR-2: User can remove a product from the cart.
- FR-3: User can update quantity of a cart item.
- FR-4: User can reorder items within the cart (drag/move up-down).
- FR-5: Cart persists across sessions (tied to user account or session token).
- FR-6: Cart displays running subtotal, tax estimate, and total.
- FR-7: User can clear the entire cart.

### 6.2 Order History
- FR-8: On checkout, cart converts into an immutable Order record.
- FR-9: User can view a list of past orders, sorted by date (most recent first).
- FR-10: User can view details of a specific order (items, quantities, price, status).
- FR-11: User can re-add all items from a past order back into the cart ("Reorder").
- FR-12: Order status is trackable (Placed → Processing → Shipped → Delivered → Cancelled/Returned).

### 6.3 Recommendations
- FR-13: System recommends products related to items in the user's cart.
- FR-14: System recommends products related to items in the user's order history.
- FR-15: Recommendations are based on a product relationship graph (e.g., "frequently bought together," "same category," "viewed together").
- FR-16: Recommendations update as the cart changes.
- FR-17: A minimum of 4 and maximum of 10 recommended items are shown per context.

## 7. Non-Functional Requirements

- **Performance:** Cart operations respond in <100ms; recommendation queries in <300ms.
- **Scalability:** Support graphs with 100k+ product nodes without full-graph scans per request.
- **Reliability:** Cart state must not be lost on network hiccups (local + server sync).
- **Maintainability:** Data structure implementations isolated behind clear interfaces/services.
- **Security:** Cart/order data scoped strictly to authenticated user/session.

## 8. User Flows

1. **Add to Cart:** Product page → "Add to Cart" → Cart linked list appends node → Cart icon updates count.
2. **Checkout:** Cart page → "Checkout" → Cart traversed, Order object created → Cart cleared → Order saved to history.
3. **View History:** Account page → "Order History" → List of past orders (linked list or indexed store) → Select order → Detail view.
4. **Reorder:** Order detail → "Reorder" → All items pushed back into cart linked list.
5. **Recommendations:** Cart/Product/Order page → Graph traversal from current item(s) → Top-N related products displayed.

## 9. Assumptions & Constraints

- Single-currency, single-region catalog for v1.
- Product catalog and inventory are provided by an external/mock service.
- Graph relationships are seeded from historical co-purchase data (batch job), not real-time ML.

## 10. Open Questions

- Should recommendations weight recency of purchase vs. frequency of co-purchase?
- Should guest (non-logged-in) users get a persisted cart, and for how long?
- What is the policy for out-of-stock items in a saved cart?

## 11. Success Criteria for v1 Launch

- Cart supports add/remove/update/reorder with correct linked-list semantics.
- Order history accurately reflects completed checkouts.
- Recommendation panel shows graph-derived, relevant products on cart and order pages.
- All core flows covered by unit and integration tests.
