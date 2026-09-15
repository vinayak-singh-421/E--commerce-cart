"""
Lightweight REST API server for the E-Commerce Cart & Order System.
Serves:
1. Cart (Doubly Linked List + O(1) Hash Map Index)
2. Order History (Append-Only Singly Linked List)
3. Recommendation Engine (Adjacency-List Graph + Co-purchase miner)
"""
import os
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from cart_linked_list import DoublyLinkedListCart
from order_history import OrderHistoryList, OrderStatus
from product_graph import ProductGraph, seed_product_graph, EdgeType

PORT = 8000
CART_FILE = os.path.join(os.path.dirname(__file__), "cart_storage.json")
ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders_storage.json")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "public")

SAMPLE_CATALOG = [
    {
        "id": "prod_kb",
        "name": "Mechanical RGB Keyboard",
        "category": "Peripherals",
        "price": 89.99,
        "image": "⌨️",
        "description": "Hot-swappable linear switches with per-key RGB backlighting."
    },
    {
        "id": "prod_mouse",
        "name": "Ergonomic Wireless Mouse",
        "category": "Peripherals",
        "price": 49.99,
        "image": "🖱️",
        "description": "High-precision 26,000 DPI sensor with ultra-low latency wireless."
    },
    {
        "id": "prod_monitor",
        "name": "27-inch 4K UHD Monitor",
        "category": "Displays",
        "price": 329.99,
        "image": "🖥️",
        "description": "IPS panel, 144Hz refresh rate, 99% sRGB color accuracy."
    },
    {
        "id": "prod_headphones",
        "name": "ANC Wireless Headphones",
        "category": "Audio",
        "price": 149.99,
        "image": "🎧",
        "description": "Active noise cancellation with 40-hour battery life and spatial audio."
    },
    {
        "id": "prod_hub",
        "name": "10-in-1 USB-C Docking Station",
        "category": "Accessories",
        "price": 64.99,
        "image": "🔌",
        "description": "Dual 4K HDMI, 100W Power Delivery pass-through, Gigabit Ethernet."
    },
    {
        "id": "prod_mat",
        "name": "Extended Desk Mat (XXL)",
        "category": "Accessories",
        "price": 24.99,
        "image": "🔲",
        "description": "Stitched edges with waterproof micro-textured cloth surface."
    }
]

CATALOG_MAP = {p["id"]: p for p in SAMPLE_CATALOG}

# Initialize In-Memory Data Structures
cart = DoublyLinkedListCart(user_id="shopper_1")
order_history = OrderHistoryList(user_id="shopper_1")
product_graph = ProductGraph()

# Load persistent Cart if exists
if os.path.exists(CART_FILE):
    try:
        with open(CART_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            cart = DoublyLinkedListCart.from_dict(data)
            print(f"[Storage] Loaded {cart.size} cart items from {CART_FILE}")
    except Exception as e:
        print(f"[Storage] Could not load {CART_FILE}: {e}")
else:
    # Initial seeds
    cart.add_item("prod_kb", "Mechanical RGB Keyboard", 1, 89.99)
    cart.add_item("prod_mouse", "Ergonomic Wireless Mouse", 1, 49.99)

# Load persistent Orders if exists
if os.path.exists(ORDERS_FILE):
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            order_history = OrderHistoryList.from_list(data, user_id="shopper_1")
            print(f"[Storage] Loaded {order_history.count} orders from {ORDERS_FILE}")
    except Exception as e:
        print(f"[Storage] Could not load {ORDERS_FILE}: {e}")

# Build initial Graph (Catalog metadata + historical co-purchases)
seed_product_graph(product_graph, SAMPLE_CATALOG, order_history.get_orders())
print(f"[Graph] Initialized with {len(product_graph.adjacency)} nodes")


def save_cart():
    try:
        with open(CART_FILE, "w", encoding="utf-8") as f:
            json.dump(cart.to_dict(), f, indent=2)
    except Exception as e:
        print(f"[Storage] Error saving cart: {e}")


def save_orders():
    try:
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(order_history.to_list(), f, indent=2)
    except Exception as e:
        print(f"[Storage] Error saving orders: {e}")


class CartRequestHandler(BaseHTTPRequestHandler):

    def _send_json(self, status_code: int, payload: dict):
        response_bytes = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_body_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw_body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            try:
                cleaned = raw_body.replace('\\"', '"').strip('\'"')
                return json.loads(cleaned)
            except Exception:
                return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. Cart Summary API
        if path == "/api/cart":
            self._send_json(200, {
                "success": True,
                "cart": cart.get_summary()
            })
            return

        # 2. Product Catalog API
        if path == "/api/catalog":
            self._send_json(200, {
                "success": True,
                "catalog": SAMPLE_CATALOG
            })
            return

        # 3. Order History API
        if path == "/api/orders":
            self._send_json(200, {
                "success": True,
                "count": order_history.count,
                "orders": order_history.get_orders()
            })
            return

        # 4. Single Order Detail API
        if path.startswith("/api/orders/") and not path.endswith("/reorder"):
            order_id = path.split("/")[-1]
            order_node = order_history.get_order_node(order_id)
            if order_node:
                self._send_json(200, {
                    "success": True,
                    "order": order_node.to_dict()
                })
            else:
                self._send_json(404, {
                    "success": False,
                    "error": f"Order {order_id} not found"
                })
            return

        # 5. Recommendation Engine API (FR-13 to FR-17)
        if path == "/api/recommendations":
            context = query.get("context", ["cart"])[0]

            if context == "cart":
                seeds = [it.product_id for it in cart.traverse()]
                exclude = set(seeds)
                recs = product_graph.recommend(
                    seed_product_ids=seeds,
                    exclude_product_ids=exclude,
                    catalog_map=CATALOG_MAP,
                    limit=6
                )
                self._send_json(200, {
                    "success": True,
                    "context": "cart",
                    "seeds": seeds,
                    "count": len(recs),
                    "recommendations": recs
                })
                return

            elif context == "order":
                order_id = query.get("orderId", [""])[0]
                order_node = order_history.get_order_node(order_id)
                if not order_node:
                    self._send_json(404, {"success": False, "error": "Order not found"})
                    return
                seeds = [it.product_id for it in order_node.items]
                cart_items = set([it.product_id for it in cart.traverse()])
                recs = product_graph.recommend(
                    seed_product_ids=seeds,
                    exclude_product_ids=cart_items,
                    catalog_map=CATALOG_MAP,
                    limit=6
                )
                self._send_json(200, {
                    "success": True,
                    "context": "order",
                    "orderId": order_id,
                    "seeds": seeds,
                    "count": len(recs),
                    "recommendations": recs
                })
                return

        # 6. Graph Topology Data API (For Live Network Visualizer)
        if path == "/api/graph":
            self._send_json(200, {
                "success": True,
                "graph": product_graph.to_graph_data(CATALOG_MAP)
            })
            return

        # Serve static files from public/
        if path == "/":
            filepath = os.path.join(STATIC_DIR, "index.html")
        else:
            rel_path = path.lstrip("/").replace("\\", "/")
            filepath = os.path.abspath(os.path.join(STATIC_DIR, rel_path))

        # Security: Prevent directory traversal outside STATIC_DIR
        if not filepath.startswith(os.path.abspath(STATIC_DIR)):
            self._send_json(403, {"error": "Access Denied"})
            return

        if os.path.exists(filepath) and os.path.isfile(filepath):
            mime_type, _ = mimetypes.guess_type(filepath)
            mime_type = mime_type or "application/octet-stream"
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self._send_json(404, {"error": "Not Found", "path": path})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Checkout Flow: Convert Cart Linked List -> Immutable Order Node + Update Co-purchase Graph
        if path == "/api/orders/checkout":
            if cart.size == 0:
                self._send_json(400, {
                    "success": False,
                    "error": "Cannot checkout: Cart is empty"
                })
                return

            order_node = order_history.checkout(cart)
            save_cart()
            save_orders()

            # Dynamic Graph Update: Increment BOUGHT_TOGETHER edges for all pairs in this order!
            if len(order_node.items) > 1:
                product_graph.record_co_purchases(order_node.items, weight_increment=2.0)
                print(f"[Graph] Mined co-purchases from checkout of {order_node.order_id}")

            self._send_json(200, {
                "success": True,
                "message": f"Order {order_node.order_id} placed successfully!",
                "order": order_node.to_dict(),
                "cart": cart.get_summary(),
                "orderCount": order_history.count
            })
            return

        # Reorder Flow: Order -> Repopulate Cart Linked List
        if path.startswith("/api/orders/") and path.endswith("/reorder"):
            parts = path.strip("/").split("/")
            order_id = parts[2]
            success = order_history.reorder(order_id, cart)
            if success:
                save_cart()
                self._send_json(200, {
                    "success": True,
                    "message": f"Reordered all items from order {order_id}",
                    "cart": cart.get_summary()
                })
            else:
                self._send_json(404, {
                    "success": False,
                    "error": f"Order {order_id} not found"
                })
            return

        # Cart Add Item
        if path == "/api/cart/items":
            data = self._read_body_json()
            product_id = data.get("productId")
            name = data.get("name", "Product")

            if not product_id:
                self._send_json(400, {"success": False, "error": "productId is required"})
                return

            try:
                quantity = int(data.get("quantity", 1))
                unit_price = float(data.get("unitPrice", 0.0))
            except (ValueError, TypeError):
                self._send_json(400, {"success": False, "error": "Invalid quantity or unit price: must be numbers"})
                return

            if quantity <= 0:
                self._send_json(400, {"success": False, "error": "Quantity must be greater than 0"})
                return

            # Bug #2 Fix: Reject negative prices before hitting the data layer
            if unit_price < 0:
                self._send_json(400, {"success": False, "error": "Unit price cannot be negative"})
                return

            try:
                cart.add_item(product_id, name, quantity, unit_price)
            except ValueError as ve:
                self._send_json(400, {"success": False, "error": str(ve)})
                return

            save_cart()
            self._send_json(200, {
                "success": True,
                "message": f"Added {name} to cart",
                "cart": cart.get_summary()
            })
            return

        # Cart Move Item (Swap Adjacent)
        if path.startswith("/api/cart/items/") and path.endswith("/move"):
            parts = path.strip("/").split("/")
            product_id = parts[3]
            data = self._read_body_json()
            direction = data.get("direction", "up")

            success = cart.move_item(product_id, direction)
            if success:
                save_cart()
                self._send_json(200, {
                    "success": True,
                    "message": f"Moved {product_id} {direction}",
                    "cart": cart.get_summary()
                })
            else:
                self._send_json(400, {
                    "success": False,
                    "error": f"Cannot move {product_id} {direction} (already at boundary or item not found)",
                    "cart": cart.get_summary()
                })
            return

        # Cart Clear
        if path == "/api/cart/clear":
            cart.clear()
            save_cart()
            self._send_json(200, {
                "success": True,
                "message": "Cart cleared",
                "cart": cart.get_summary()
            })
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Order Status Tracking Update (Placed -> Processing -> Shipped -> Delivered)
        if path.startswith("/api/orders/") and path.endswith("/status"):
            parts = path.strip("/").split("/")
            order_id = parts[2]
            data = self._read_body_json()
            new_status = data.get("status", "")

            try:
                success = order_history.update_status(order_id, new_status)
                if success:
                    save_orders()
                    order_node = order_history.get_order_node(order_id)
                    self._send_json(200, {
                        "success": True,
                        "message": f"Order {order_id} status updated to {new_status}",
                        "order": order_node.to_dict()
                    })
                else:
                    self._send_json(404, {
                        "success": False,
                        "error": f"Order {order_id} not found"
                    })
            except ValueError as ve:
                self._send_json(400, {
                    "success": False,
                    "error": str(ve)
                })
            return

        # Cart Update Quantity
        if path.startswith("/api/cart/items/"):
            product_id = path.split("/")[-1]
            data = self._read_body_json()
            try:
                quantity = int(data.get("quantity", 1))
            except (ValueError, TypeError):
                self._send_json(400, {
                    "success": False,
                    "error": "Invalid quantity: must be an integer"
                })
                return

            try:
                success = cart.update_quantity(product_id, quantity)
            except ValueError as ve:
                self._send_json(400, {"success": False, "error": str(ve)})
                return

            if success:
                save_cart()
                self._send_json(200, {
                    "success": True,
                    "message": f"Updated {product_id} quantity to {quantity}",
                    "cart": cart.get_summary()
                })
            else:
                self._send_json(404, {
                    "success": False,
                    "error": f"Product {product_id} not found in cart",
                    "cart": cart.get_summary()
                })
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Cart Remove Item
        if path.startswith("/api/cart/items/"):
            product_id = path.split("/")[-1]
            success = cart.remove_item(product_id)
            if success:
                save_cart()
                self._send_json(200, {
                    "success": True,
                    "message": f"Removed {product_id} from cart",
                    "cart": cart.get_summary()
                })
            else:
                self._send_json(404, {
                    "success": False,
                    "error": f"Product {product_id} not found in cart",
                    "cart": cart.get_summary()
                })
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, CartRequestHandler)
    print(f"=== E-commerce Cart & Order System Server (Phases 1, 2, 3) ===")
    print(f"Running at: http://localhost:{PORT}")
    print(f"Serving UI from: {STATIC_DIR}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
