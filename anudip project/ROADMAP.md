# Roadmap
## E-commerce Cart & Order System

**Version:** 1.0
**Last Updated:** 2026-09-14

---

## Guiding Principle

Ship the core data-structure-driven functionality first (Cart via Linked List), then layer on Order History, then Recommendations (Graph), then optimize/scale.

---

## Phase 0 — Project Setup (Week 1)

- [ ] Repo scaffolding, CI/CD pipeline
- [ ] Choose & set up stack (backend framework, Postgres, Redis)
- [ ] Define API contracts (OpenAPI/GraphQL schema)
- [ ] Set up base data models (`users`, `products` seed data)

**Deliverable:** Empty but running skeleton service + DB schema.

---

## Phase 1 — Cart Module (Linked List) (Weeks 2–3)

- [ ] Implement Doubly Linked List `CartItemNode` / `Cart` classes
- [ ] Implement `nodeIndex` hash map for O(1) lookups
- [ ] API: add / remove / update quantity / reorder / clear / get cart
- [ ] Redis write-through caching for active cart
- [ ] Postgres durable backup of cart state
- [ ] Unit tests for all linked-list edge cases (empty, single node, head/tail ops)
- [ ] Frontend: Cart UI (add/remove/reorder/quantity controls)

**Deliverable:** Fully functional, persistent shopping cart.

---

## Phase 2 — Order History (Weeks 4–5)

- [ ] Checkout flow: Cart → immutable Order snapshot
- [ ] `orders` / `order_items` tables + indexes
- [ ] API: list orders (paginated, recency order), get order detail
- [ ] "Reorder" flow: rehydrate cart from past order
- [ ] Order status lifecycle (Placed → Processing → Shipped → Delivered)
- [ ] Frontend: Order history list + detail views

**Deliverable:** Users can complete checkout and review/reorder past purchases.

---

## Phase 3 — Recommendation Engine (Graph) (Weeks 6–8)

- [ ] Design `product_edges` schema (weight, type)
- [ ] Build Graph Builder batch job (co-purchase + same-category edges)
- [ ] Implement in-memory adjacency-list Graph + neighbor ranking
- [ ] API: `GET /recommendations?context=cart|order`
- [ ] Recommendation merge/ranking algorithm (multi-seed aggregation)
- [ ] Frontend: "You might also like" panel on cart & order pages
- [ ] A/B test setup to measure click-through rate

**Deliverable:** Graph-backed recommendations live on cart and order pages.

---

## Phase 4 — Hardening & Polish (Weeks 9–10)

- [ ] Load testing (cart mutation throughput, recommendation latency)
- [ ] Error handling pass (out-of-stock, concurrent cart edits, expired sessions)
- [ ] Observability: logging, metrics, alerting on cart/order/recommendation services
- [ ] Security review (auth scoping, rate limiting)
- [ ] Full regression + integration test suite

**Deliverable:** Production-ready v1 release.

---

## Phase 5 — v2 Enhancements (Post-launch)

- [ ] Incremental/real-time graph edge updates (vs. nightly batch)
- [ ] Multi-hop / weighted-path recommendations (deeper graph traversal)
- [ ] Guest cart support with expiry policy
- [ ] Personalized ranking (blend graph signals with user-level ML model)
- [ ] Cart sharding / Redis cluster scaling
- [ ] Consider dedicated graph database (e.g., Neo4j, Redis Graph) if catalog scale demands it

---

## Milestones Summary

| Milestone | Target | Key Data Structure |
|---|---|---|
| M1: Cart MVP | End of Week 3 | Doubly Linked List |
| M2: Order History MVP | End of Week 5 | Linked List (append-only) / DB |
| M3: Recommendations MVP | End of Week 8 | Graph (adjacency list) |
| M4: v1 Launch | End of Week 10 | — |
| M5: v2 Kickoff | Post-launch | Graph DB / ML exploration |
