/**
 * Interactive Client Controller for Cart, Order History & Recommendation Engine
 * Full End-to-End System (Phases 1, 2, 3)
 */

const API_BASE = "";

// State
let catalogData = [];
let currentCart = null;
let ordersData = [];
let graphData = null;
let recommendationsData = [];

// Element references - Tabs
const tabCartBtn = document.getElementById("tab-cart");
const tabOrdersBtn = document.getElementById("tab-orders");
const tabGraphBtn = document.getElementById("tab-graph");

const tabCartBadge = document.getElementById("tab-cart-badge");
const tabOrdersBadge = document.getElementById("tab-orders-badge");
const tabGraphBadge = document.getElementById("tab-graph-badge");

const viewCart = document.getElementById("view-cart");
const viewOrders = document.getElementById("view-orders");
const viewGraph = document.getElementById("view-graph");

// Cart Elements
const catalogListEl = document.getElementById("catalog-list");
const cartItemListEl = document.getElementById("cart-item-list");
const cartEmptyMsgEl = document.getElementById("cart-empty-message");
const linkedListVizEl = document.getElementById("linked-list-viz");
const hashmapEntriesEl = document.getElementById("hashmap-entries");
const logTextEl = document.getElementById("log-text");

const statNodeCountEl = document.getElementById("stat-node-count");
const statQtyCountEl = document.getElementById("stat-qty-count");
const valSubtotalEl = document.getElementById("val-subtotal");
const valTaxEl = document.getElementById("val-tax");
const valTotalEl = document.getElementById("val-total");

const btnClearCart = document.getElementById("btn-clear-cart");
const btnCheckout = document.getElementById("btn-checkout");

// Recommendations Elements
const recsGridEl = document.getElementById("recommendations-grid");
const recsEmptyEl = document.getElementById("recommendations-empty");

// Order History Elements
const ordersSinglyChainEl = document.getElementById("orders-singly-chain");
const ordersCardsListEl = document.getElementById("orders-cards-list");
const ordersEmptyMsgEl = document.getElementById("orders-empty-message");
const ordersCountLabel = document.getElementById("orders-count-label");

// Graph Explorer Elements
const graphAdjacencyListEl = document.getElementById("graph-adjacency-list");

// Generate stable pseudo memory address for visual realism (e.g. 0x7FA1)
function getMockAddress(id) {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash << 5) - hash + id.charCodeAt(i);
    hash |= 0;
  }
  const hex = (Math.abs(hash) % 65535).toString(16).toUpperCase().padStart(4, "0");
  return `0x${hex}`;
}

// Log an operation with timestamp and complexity
function logAction(actionText, complexity = "O(1)") {
  const time = new Date().toLocaleTimeString();
  logTextEl.innerHTML = `<span style="color: #64748b;">[${time}]</span> <span style="color: #f59e0b; font-weight: 700;">[${complexity}]</span> ${actionText}`;
}

// Tab Switching
function switchTab(target) {
  [tabCartBtn, tabOrdersBtn, tabGraphBtn].forEach(b => b.classList.remove("active"));
  [viewCart, viewOrders, viewGraph].forEach(v => v.style.display = "none");

  if (target === "cart") {
    tabCartBtn.classList.add("active");
    viewCart.style.display = "flex";
  } else if (target === "orders") {
    tabOrdersBtn.classList.add("active");
    viewOrders.style.display = "flex";
    loadOrders();
  } else if (target === "graph") {
    tabGraphBtn.classList.add("active");
    viewGraph.style.display = "flex";
    loadGraph();
  }
}

tabCartBtn.addEventListener("click", () => switchTab("cart"));
tabOrdersBtn.addEventListener("click", () => switchTab("orders"));
tabGraphBtn.addEventListener("click", () => switchTab("graph"));

// 1. Fetch Catalog
async function loadCatalog() {
  try {
    const res = await fetch(`${API_BASE}/api/catalog`);
    const data = await res.json();
    if (data.success) {
      catalogData = data.catalog;
      renderCatalog();
    }
  } catch (err) {
    console.error("Error loading catalog:", err);
    catalogListEl.innerHTML = `<div class="error-msg">Failed to connect to backend server.</div>`;
  }
}

// 2. Fetch Cart
async function loadCart() {
  try {
    const res = await fetch(`${API_BASE}/api/cart`);
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      loadRecommendations();
    }
  } catch (err) {
    console.error("Error loading cart:", err);
  }
}

// 3. Fetch Orders
async function loadOrders() {
  try {
    const res = await fetch(`${API_BASE}/api/orders`);
    const data = await res.json();
    if (data.success) {
      ordersData = data.orders;
      tabOrdersBadge.textContent = data.count;
      renderOrders();
    }
  } catch (err) {
    console.error("Error loading orders:", err);
  }
}

// 4. Fetch Recommendations (FR-13 to FR-17)
async function loadRecommendations() {
  try {
    const res = await fetch(`${API_BASE}/api/recommendations?context=cart`);
    const data = await res.json();
    if (data.success) {
      recommendationsData = data.recommendations;
      renderRecommendations();
    }
  } catch (err) {
    console.error("Error loading recommendations:", err);
  }
}

// 5. Fetch Graph Topology
async function loadGraph() {
  try {
    const res = await fetch(`${API_BASE}/api/graph`);
    const data = await res.json();
    if (data.success) {
      graphData = data.graph;
      tabGraphBadge.textContent = `${graphData.edgeCount} Edges`;
      renderGraph();
    }
  } catch (err) {
    console.error("Error loading graph:", err);
  }
}

// 6. Render Catalog
function renderCatalog() {
  catalogListEl.innerHTML = "";
  catalogData.forEach(prod => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <div class="prod-emoji">${prod.image}</div>
      <div class="prod-category">${prod.category}</div>
      <h3 class="prod-name">${prod.name}</h3>
      <p class="prod-desc">${prod.description}</p>
      <div class="prod-footer">
        <span class="prod-price">$${prod.price.toFixed(2)}</span>
        <button class="btn-add-cart" onclick="handleAddToCart('${prod.id}')">
          + Add to Cart
        </button>
      </div>
    `;
    catalogListEl.appendChild(card);
  });
}

// 7. Render Cart
function renderCart() {
  if (!currentCart) return;

  tabCartBadge.textContent = currentCart.size;
  statNodeCountEl.textContent = currentCart.size;
  statQtyCountEl.textContent = currentCart.totalQuantity;
  valSubtotalEl.textContent = `$${currentCart.subtotal.toFixed(2)}`;
  valTaxEl.textContent = `$${currentCart.taxEstimate.toFixed(2)}`;
  valTotalEl.textContent = `$${currentCart.total.toFixed(2)}`;

  cartItemListEl.innerHTML = "";

  if (currentCart.size === 0) {
    cartEmptyMsgEl.style.display = "block";
    cartItemListEl.style.display = "none";
    btnCheckout.disabled = true;
    btnCheckout.style.opacity = "0.5";
    btnCheckout.style.cursor = "not-allowed";
    return;
  }

  btnCheckout.disabled = false;
  btnCheckout.style.opacity = "1";
  btnCheckout.style.cursor = "pointer";

  cartEmptyMsgEl.style.display = "none";
  cartItemListEl.style.display = "flex";

  const items = currentCart.items;
  items.forEach((item, index) => {
    const isFirst = index === 0;
    const isLast = index === items.length - 1;

    const row = document.createElement("div");
    row.className = "cart-item-row";
    row.innerHTML = `
      <div class="reorder-controls">
        <button class="btn-arrow" title="Move Up (Swap with Prev Node)" onclick="handleMoveItem('${item.productId}', 'up')" ${isFirst ? "disabled" : ""}>
          ▲
        </button>
        <button class="btn-arrow" title="Move Down (Swap with Next Node)" onclick="handleMoveItem('${item.productId}', 'down')" ${isLast ? "disabled" : ""}>
          ▼
        </button>
      </div>
      <div class="node-pos-pill">#${index + 1}</div>
      <div class="cart-item-info">
        <div class="cart-item-title">${item.name}</div>
        <div class="cart-item-meta">${item.productId} &bull; $${item.unitPrice.toFixed(2)} ea</div>
      </div>
      <div class="cart-qty-ctrls">
        <button class="btn-qty" onclick="handleUpdateQty('${item.productId}', ${item.quantity - 1})">-</button>
        <span class="qty-display">${item.quantity}</span>
        <button class="btn-qty" onclick="handleUpdateQty('${item.productId}', ${item.quantity + 1})">+</button>
      </div>
      <div class="cart-item-price">$${item.totalPrice.toFixed(2)}</div>
      <button class="btn-delete" title="Unlink & Remove Node (O(1))" onclick="handleRemoveItem('${item.productId}')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
      </button>
    `;
    cartItemListEl.appendChild(row);
  });
}

// 8. Render Doubly Linked List Visualizer
function renderVisualizer() {
  if (!currentCart) return;

  linkedListVizEl.innerHTML = "";

  if (currentCart.size === 0) {
    linkedListVizEl.innerHTML = `
      <div class="null-node-marker">HEAD ➔ NULL &nbsp;|&nbsp; TAIL ➔ NULL (Empty List)</div>
    `;
    hashmapEntriesEl.innerHTML = `<span style="font-size: 0.78rem; color: #64748b;">Hash map index is empty.</span>`;
    return;
  }

  // Prepend NULL indicator for head.prev
  const nullStart = document.createElement("div");
  nullStart.className = "null-node-marker";
  nullStart.textContent = "NULL";
  linkedListVizEl.appendChild(nullStart);

  const items = currentCart.items;

  items.forEach((item, index) => {
    const isHead = item.productId === currentCart.headProductId;
    const isTail = item.productId === currentCart.tailProductId;
    const memAddr = getMockAddress(item.productId);

    // Connector from prev
    const connector = document.createElement("div");
    connector.className = "pointer-connector";
    connector.innerHTML = `<div class="arrow-link">⇄</div>`;
    linkedListVizEl.appendChild(connector);

    // Node card
    const nodeWrapper = document.createElement("div");
    nodeWrapper.className = "node-card-wrapper";
    nodeWrapper.innerHTML = `
      <div class="node-card ${isHead ? 'is-head' : ''} ${isTail ? 'is-tail' : ''}">
        <div class="node-header-tags">
          <div>
            ${isHead ? '<span class="node-pointer-tag tag-head">HEAD</span>' : ''}
            ${isTail ? '<span class="node-pointer-tag tag-tail">TAIL</span>' : ''}
          </div>
          <span class="node-mem-addr">${memAddr}</span>
        </div>
        <div class="node-content-box">
          <div class="node-prop">
            <span>Product:</span>
            <span class="node-prop-id">${item.productId}</span>
          </div>
          <div class="node-prop">
            <span>Name:</span>
            <strong>${item.name.substring(0, 16)}...</strong>
          </div>
          <div class="node-prop">
            <span>Qty &times; Price:</span>
            <strong>${item.quantity} &times; $${item.unitPrice.toFixed(2)}</strong>
          </div>
        </div>
        <div class="node-pointers-meta">
          <div class="pointer-indicator ${item.hasPrev ? 'has-link' : 'null-link'}">
            prev: ${item.prevProductId ? item.prevProductId : 'NULL'}
          </div>
          <div class="pointer-indicator ${item.hasNext ? 'has-link' : 'null-link'}">
            next: ${item.nextProductId ? item.nextProductId : 'NULL'}
          </div>
        </div>
      </div>
    `;
    linkedListVizEl.appendChild(nodeWrapper);
  });

  // Append NULL indicator for tail.next
  const tailConnector = document.createElement("div");
  tailConnector.className = "pointer-connector";
  tailConnector.innerHTML = `<div class="arrow-link">⇄</div>`;
  linkedListVizEl.appendChild(tailConnector);

  const nullEnd = document.createElement("div");
  nullEnd.className = "null-node-marker";
  nullEnd.textContent = "NULL";
  linkedListVizEl.appendChild(nullEnd);

  // Render Hash Map Entries
  renderHashMap();
}

// 9. Render Hash Map Inspector
function renderHashMap() {
  hashmapEntriesEl.innerHTML = "";
  if (!currentCart.nodeIndexKeys || currentCart.nodeIndexKeys.length === 0) {
    hashmapEntriesEl.innerHTML = `<span style="font-size: 0.78rem; color: #64748b;">No keys in map</span>`;
    return;
  }

  currentCart.nodeIndexKeys.forEach(key => {
    const pill = document.createElement("div");
    pill.className = "hashmap-pill";
    pill.innerHTML = `
      <span class="hashmap-key">"${key}"</span>
      <span class="hashmap-arrow">➔</span>
      <span class="hashmap-val">${getMockAddress(key)} (CartItemNode)</span>
    `;
    hashmapEntriesEl.appendChild(pill);
  });
}

// 10. Render Recommendations (Graph Traversal Results)
function renderRecommendations() {
  recsGridEl.innerHTML = "";

  if (recommendationsData.length === 0) {
    recsEmptyEl.style.display = "block";
    recsGridEl.style.display = "none";
    return;
  }

  recsEmptyEl.style.display = "none";
  recsGridEl.style.display = "grid";

  recommendationsData.forEach(rec => {
    const card = document.createElement("div");
    card.className = "rec-card";
    card.innerHTML = `
      <div class="rec-card-top">
        <span class="rec-emoji">${rec.image}</span>
        <span class="rec-score-badge">Affinity Score: ${rec.score}</span>
      </div>
      <h4 class="rec-name">${rec.name}</h4>
      <div class="rec-reason-pill">
        <span>⚡</span> ${rec.primaryReason}
      </div>
      <div class="rec-card-footer">
        <span class="rec-price">$${rec.price.toFixed(2)}</span>
        <button class="btn-add-rec" onclick="handleAddToCart('${rec.productId}')">
          + Add to Cart
        </button>
      </div>
    `;
    recsGridEl.appendChild(card);
  });
}

// 11. Render Order History
function renderOrders() {
  ordersCountLabel.textContent = `${ordersData.length} Orders Recorded`;
  tabOrdersBadge.textContent = ordersData.length;

  if (ordersData.length === 0) {
    ordersEmptyMsgEl.style.display = "block";
    ordersCardsListEl.style.display = "none";
    ordersSinglyChainEl.innerHTML = `<div class="null-node-marker">HEAD ➔ NULL (No Orders Placed)</div>`;
    return;
  }

  ordersEmptyMsgEl.style.display = "none";
  ordersCardsListEl.style.display = "grid";

  // Singly Linked List Recency Pipeline
  ordersSinglyChainEl.innerHTML = "";
  ordersData.forEach((ord, index) => {
    const isHead = index === 0;

    const nodeCard = document.createElement("div");
    nodeCard.className = `singly-node-card ${isHead ? 'is-head' : ''}`;
    nodeCard.innerHTML = `
      <div class="singly-node-header">
        <span class="singly-order-id">${ord.orderId}</span>
        ${isHead ? '<span class="singly-head-badge">HEAD (Newest)</span>' : ''}
      </div>
      <div class="singly-node-meta">
        <span>Items: ${ord.totalQuantity}</span>
        <strong style="color: var(--accent-emerald);">$${ord.total.toFixed(2)}</strong>
      </div>
      <div class="singly-pointer-meta">
        next ➔ ${ord.nextOrderId ? ord.nextOrderId : 'NULL'}
      </div>
    `;
    ordersSinglyChainEl.appendChild(nodeCard);

    const arrow = document.createElement("div");
    arrow.className = "singly-arrow";
    arrow.innerHTML = "➔";
    ordersSinglyChainEl.appendChild(arrow);
  });

  const nullMarker = document.createElement("div");
  nullMarker.className = "null-node-marker";
  nullMarker.textContent = "NULL (Oldest)";
  ordersSinglyChainEl.appendChild(nullMarker);

  // Order Detail Cards
  ordersCardsListEl.innerHTML = "";
  ordersData.forEach(ord => {
    const dateStr = new Date(ord.createdAt).toLocaleString();
    const statusLower = ord.status.toLowerCase();

    const steps = ["PLACED", "PROCESSING", "SHIPPED", "DELIVERED"];
    const currentStepIdx = steps.indexOf(ord.status);

    const card = document.createElement("div");
    card.className = "order-card";
    card.innerHTML = `
      <div class="order-card-header">
        <div class="order-card-id-block">
          <span class="order-card-id">${ord.orderId}</span>
          <span class="order-card-time">${dateStr}</span>
        </div>
        <span class="status-pill status-${statusLower}">
          ● ${ord.status}
        </span>
      </div>

      <!-- Lifecycle Stepper -->
      <div class="order-stepper">
        ${steps.map((st, i) => {
          let stateClass = "";
          if (i < currentStepIdx) stateClass = "completed";
          else if (i === currentStepIdx) stateClass = "active";
          return `
            <div class="step-node ${stateClass}">
              <div class="step-dot"></div>
              <span>${st}</span>
            </div>
          `;
        }).join("")}
      </div>

      <!-- Items Snapshot -->
      <div class="order-items-table">
        ${ord.items.map(item => `
          <div class="order-item-snapshot-row">
            <span class="order-item-snapshot-name">${item.name}</span>
            <span class="order-item-snapshot-qty">&times; ${item.quantity}</span>
            <span class="order-item-snapshot-price">$${item.totalPrice.toFixed(2)}</span>
          </div>
        `).join("")}
      </div>

      <!-- Card Footer -->
      <div class="order-card-footer">
        <div class="order-total-block">
          <span class="order-total-label">Subtotal: $${ord.subtotal.toFixed(2)} &bull; Tax: $${ord.tax.toFixed(2)}</span>
          <span class="order-total-amount">$${ord.total.toFixed(2)}</span>
        </div>
        <div class="order-actions">
          <select class="status-select" onchange="handleUpdateOrderStatus('${ord.orderId}', this.value)" title="Simulate Order Lifecycle">
            <option value="PLACED" ${ord.status === 'PLACED' ? 'selected' : ''}>Placed</option>
            <option value="PROCESSING" ${ord.status === 'PROCESSING' ? 'selected' : ''}>Processing</option>
            <option value="SHIPPED" ${ord.status === 'SHIPPED' ? 'selected' : ''}>Shipped</option>
            <option value="DELIVERED" ${ord.status === 'DELIVERED' ? 'selected' : ''}>Delivered</option>
            <option value="CANCELLED" ${ord.status === 'CANCELLED' ? 'selected' : ''}>Cancelled</option>
          </select>
          <button class="btn-reorder" onclick="handleReorder('${ord.orderId}')" title="Push all items into active cart linked list (FR-11)">
            ⚡ Reorder
          </button>
        </div>
      </div>
    `;
    ordersCardsListEl.appendChild(card);
  });
}

// 12. Render Product Graph Topology
function renderGraph() {
  if (!graphData) return;

  graphAdjacencyListEl.innerHTML = "";

  graphData.nodes.forEach(node => {
    // Find all outgoing edges from this node
    const outgoing = graphData.edges.filter(e => e.source === node.id || e.target === node.id);

    const block = document.createElement("div");
    block.className = "graph-node-block";
    block.innerHTML = `
      <div class="graph-node-header">
        <div class="graph-node-title">
          <span>${node.image}</span>
          <span>${node.label}</span>
        </div>
        <span class="graph-node-degree">Degree: ${node.degree}</span>
      </div>
      <div class="graph-edges-list">
        ${outgoing.map(e => {
          const neighborId = e.source === node.id ? e.target : e.source;
          const neighborProd = catalogData.find(p => p.id === neighborId);
          const neighborName = neighborProd ? neighborProd.name : neighborId;
          const typeClass = e.type === "BOUGHT_TOGETHER" ? "tag-bought" : (e.type === "VIEWED_TOGETHER" ? "tag-viewed" : "tag-category");

          return `
            <div class="graph-edge-item">
              <span class="graph-edge-target">➔ ${neighborName}</span>
              <div class="graph-edge-badges">
                <span class="graph-legend-tag ${typeClass}">${e.type}</span>
                <span class="edge-weight-badge">w=${e.weight}</span>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;
    graphAdjacencyListEl.appendChild(block);
  });
}

// --- API ACTIONS ---

// Add to Cart
async function handleAddToCart(productId) {
  const product = catalogData.find(p => p.id === productId);
  if (!product) return;

  try {
    const res = await fetch(`${API_BASE}/api/cart/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        productId: product.id,
        name: product.name,
        quantity: 1,
        unitPrice: product.price
      })
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      loadRecommendations();
      logAction(`Appended/Updated <strong>${product.name}</strong> (${product.id}) via hash map index & tail pointer.`, "O(1)");
    }
  } catch (err) {
    console.error("Add item error:", err);
  }
}

// Remove from Cart
async function handleRemoveItem(productId) {
  try {
    const res = await fetch(`${API_BASE}/api/cart/items/${productId}`, {
      method: "DELETE"
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      loadRecommendations();
      logAction(`Unlinked pointers (prev.next = next, next.prev = prev) and dropped node <strong>${productId}</strong>.`, "O(1)");
    }
  } catch (err) {
    console.error("Remove item error:", err);
  }
}

// Update Quantity
async function handleUpdateQty(productId, newQty) {
  try {
    const res = await fetch(`${API_BASE}/api/cart/items/${productId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quantity: newQty })
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      loadRecommendations();
      if (newQty <= 0) {
        logAction(`Quantity reached 0 &bull; Auto-removed node <strong>${productId}</strong> from list & index.`, "O(1)");
      } else {
        logAction(`Located node in hash map & updated quantity of <strong>${productId}</strong> to ${newQty}.`, "O(1)");
      }
    }
  } catch (err) {
    console.error("Update qty error:", err);
  }
}

// Move Item (Swap Adjacent)
async function handleMoveItem(productId, direction) {
  try {
    const res = await fetch(`${API_BASE}/api/cart/items/${productId}/move`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ direction })
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      logAction(`Swapped adjacent pointers for node <strong>${productId}</strong> (${direction}ward swap).`, "O(1)");
    } else {
      logAction(`Could not move ${productId} ${direction}: ${data.error}`, "O(1)");
    }
  } catch (err) {
    console.error("Move item error:", err);
  }
}

// Clear Cart
btnClearCart.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to clear the cart?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/cart/clear`, {
      method: "POST"
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      loadRecommendations();
      logAction("Cleared all pointers: head = null, tail = null, nodeIndex.clear().", "O(1)");
    }
  } catch (err) {
    console.error("Clear cart error:", err);
  }
});

// Checkout Flow (FR-8: Cart -> Immutable Order Record + Co-purchase Graph update)
btnCheckout.addEventListener("click", async () => {
  if (!currentCart || currentCart.size === 0) {
    alert("Cart is empty! Add items first.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/orders/checkout`, {
      method: "POST"
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      loadRecommendations();
      loadGraph();

      logAction(`Completed Checkout! Traversed Cart ($O(n)$), froze snapshot into <strong>${data.order.orderId}</strong>, updated co-purchase Graph edges, and prepended to Order Singly Linked List ($O(1)$).`, "O(n) + O(1)");

      await loadOrders();
      switchTab("orders");
    } else {
      alert(`Checkout failed: ${data.error}`);
    }
  } catch (err) {
    console.error("Checkout error:", err);
  }
});

// Reorder Flow (FR-11: Order -> Rehydrate Cart Linked List)
async function handleReorder(orderId) {
  try {
    const res = await fetch(`${API_BASE}/api/orders/${orderId}/reorder`, {
      method: "POST"
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.cart;
      renderCart();
      renderVisualizer();
      loadRecommendations();

      logAction(`Reordered all items from <strong>${orderId}</strong>! Repopulated Doubly Linked List cart.`, "O(k)");
      switchTab("cart");
    }
  } catch (err) {
    console.error("Reorder error:", err);
  }
}

// Update Order Status (FR-12: Lifecycle Tracking)
async function handleUpdateOrderStatus(orderId, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/api/orders/${orderId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
      logAction(`Updated status of order <strong>${orderId}</strong> to <strong>${newStatus}</strong>.`, "O(k)");
      await loadOrders();
    }
  } catch (err) {
    console.error("Update status error:", err);
  }
}

// Initialization
window.addEventListener("DOMContentLoaded", () => {
  loadCatalog();
  loadCart();
  loadOrders();
  loadGraph();
});
