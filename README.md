# E-Commerce Cart & Order System

> An end-to-end, data-structure-driven e-commerce platform demonstrating real-world applications of **Doubly Linked Lists**, **Append-Only Singly Linked Lists**, and **In-Memory Adjacency-List Graphs**.

---

## 🎯 Project Overview & Data Structures

This system implements the complete specification outlined in `PRD.md`, `TECHNICAL.md`, and `ARCHITECTURE.md`:

| Module | Core Data Structure | Algorithmic Benefit | Real-World Application |
|---|---|---|---|
| **Shopping Cart** | **Doubly Linked List** + Supporting $O(1)$ Hash Map Index (`node_index`) | $O(1)$ append, $O(1)$ deletion, $O(1)$ adjacent swapping without array shift costs ($O(n)$) | Preserves exact sequential item ordering; enables drag-and-drop / move up/down controls. |
| **Order History** | **Append-Only Singly Linked List** (Ordered by Recency) | $O(1)$ prepending of newly placed orders to `head`; natural chronological ordering | Immutable order snapshots; status lifecycle tracking; instant one-click reordering. |
| **Recommendations** | In-Memory **Adjacency-List Graph** (`ProductGraph`) | Efficient neighbor traversal, multi-seed aggregation, dynamic co-purchase mining | Multi-type relationship modeling (`BOUGHT_TOGETHER`, `VIEWED_TOGETHER`, `SAME_CATEGORY`). |

---

## 🚀 Quick Start (Zero Dependencies)

The project is built entirely with the **Python standard library** and **Vanilla Modern Web technologies** (HTML5, CSS3, JavaScript). No `npm install` or `pip install` required!

### 1. Run the Server
```powershell
python app.py
```
The server will start on: **[http://localhost:8000](http://localhost:8000)**

### 2. Run the Automated Test Suite (29 Tests)
```powershell
python -m unittest discover -v
```

---

## 📁 Repository Structure

```text
anudip project/
├── cart_linked_list.py     # Doubly Linked List Cart implementation & nodeIndex
├── order_history.py        # Singly Linked List Order History & immutable snapshots
├── product_graph.py        # In-memory Adjacency List Graph & recommendation engine
├── app.py                  # Lightweight REST API server & static asset handler
├── test_cart.py            # Unit tests for Cart Doubly Linked List (15 tests)
├── test_orders.py          # Unit tests for Order History & Checkout (7 tests)
├── test_graph.py           # Unit tests for Recommendation Graph (7 tests)
├── cart_storage.json       # Durable session backup for shopping cart
├── orders_storage.json     # Durable session backup for order history
├── public/                 # Interactive web interface & visualizers
│   ├── index.html          # Semantic HTML layout (Cart, Orders, Graph tabs)
│   ├── style.css           # Modern dark-mode UI with glassmorphism & glowing badges
│   └── app.js              # Real-time state syncing & dynamic node visualizers
├── PRD.md                  # Product Requirements Document
├── TECHNICAL.md            # Technical Design Document
├── ARCHITECTURE.md         # Architecture Document
└── ROADMAP.md              # Milestone Roadmap
```

---

## 🧪 Requirements Realization Matrix

| Requirement | Description | Implementation Status | Complexity |
|---|---|---|---|
| **FR-1** | Add product to cart | [cart_linked_list.py](cart_linked_list.py) | $O(1)$ |
| **FR-2** | Remove product from cart | [cart_linked_list.py](cart_linked_list.py) | $O(1)$ |
| **FR-3** | Update quantity (auto-remove if $\le 0$) | [cart_linked_list.py](cart_linked_list.py) | $O(1)$ |
| **FR-4** | Reorder items (Move Up/Down) | [cart_linked_list.py](cart_linked_list.py) | $O(1)$ |
| **FR-5** | Cart persistence across sessions | [cart_storage.json](cart_storage.json) | $O(n)$ |
| **FR-6** | Subtotal, 8% tax estimate, and total | [cart_linked_list.py](cart_linked_list.py) | $O(n)$ |
| **FR-7** | Clear cart | [cart_linked_list.py](cart_linked_list.py) | $O(1)$ |
| **FR-8** | Checkout creates immutable snapshot | [order_history.py](order_history.py) | $O(n)$ |
| **FR-9** | Orders sorted by recency (newest first) | [order_history.py](order_history.py) | $O(1)$ prepend |
| **FR-10** | Order detail inspection | [order_history.py](order_history.py) | $O(k)$ |
| **FR-11** | One-click Reorder repopulates cart | [order_history.py](order_history.py) | $O(k)$ |
| **FR-12** | Order status tracking lifecycle | [order_history.py](order_history.py) | $O(k)$ |
| **FR-13** | Recommendations for cart items | [product_graph.py](product_graph.py) | $O(m \cdot k \log k)$ |
| **FR-14** | Recommendations for past orders | [product_graph.py](product_graph.py) | $O(m \cdot k \log k)$ |
| **FR-15** | Product relationship graph with edge types | [product_graph.py](product_graph.py) | $O(1)$ |
| **FR-16** | Dynamic recommendations synchronization | [public/app.js](public/app.js) | Reactive |
| **FR-17** | Filter exclusions and rank top items | [product_graph.py](product_graph.py) | $O(k \log k)$ |

---

## 🌐 Features of the Web Application

- **Live Doubly Linked List Visualizer**: Shows simulated memory addresses (`0x7FA2`), `HEAD`/`TAIL` badges, and bi-directional `⇄` pointer connections update in real time when you add, remove, or reorder items.
- **Hash Map Index Table**: Live inspector showing `nodeIndex` keys mapped to memory nodes for $O(1)$ random-access mutations.
- **Singly Linked List Chain Visualizer**: Visualizes newly checked-out orders prepending to the head of the pipeline.
- **Order Lifecycle Stepper**: Tracks milestones (*Placed $\rightarrow$ Processing $\rightarrow$ Shipped $\rightarrow$ Delivered*) with an interactive simulator dropdown.
- **Product Graph Explorer**: Visualizes all graph nodes, degrees, edge weights, and relationship types.
#
