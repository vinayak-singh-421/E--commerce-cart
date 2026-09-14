"""
Adversarial QA Test Suite: Stress Testing, Boundary Fuzzing, Security & Edge Cases
Designed to uncover potential bugs across Cart, Order History, Graph, and REST API.
"""
import urllib.request
import urllib.error
import json
import random
import unittest
from cart_linked_list import DoublyLinkedListCart
from order_history import OrderHistoryList, OrderStatus
from product_graph import ProductGraph, EdgeType, seed_product_graph

API_BASE = "http://localhost:8000"


def make_request(path, method="GET", body=None):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, method=method)
    if body is not None:
        if isinstance(body, (dict, list)):
            data_bytes = json.dumps(body).encode("utf-8")
            req.add_header("Content-Type", "application/json")
        elif isinstance(body, str):
            data_bytes = body.encode("utf-8")
            req.add_header("Content-Type", "application/json")
        else:
            data_bytes = body
        req.data = data_bytes
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", errors="replace"))
        except Exception:
            return e.code, {}
    except Exception as ex:
        return 500, {"error": str(ex)}


class QAAdversarialTestSuite(unittest.TestCase):

    # =========================================================================
    # 1. LINKED LIST ADVERSARIAL STRESS & FUZZ TESTING
    # =========================================================================

    def test_cart_fuzz_random_operations(self):
        """Fuzz test: 500 random add, remove, move, and update operations verifying integrity at every step."""
        cart = DoublyLinkedListCart("fuzz_user")
        products = [f"prod_{i}" for i in range(25)]

        for op_idx in range(500):
            action = random.choice(["add", "remove", "move_up", "move_down", "update_qty", "clear"])
            p_id = random.choice(products)

            if action == "add":
                qty = random.randint(1, 10)
                price = round(random.uniform(5.0, 500.0), 2)
                cart.add_item(p_id, f"Product {p_id}", qty, price)

            elif action == "remove":
                cart.remove_item(p_id)

            elif action == "move_up":
                cart.move_item(p_id, "up")

            elif action == "move_down":
                cart.move_item(p_id, "down")

            elif action == "update_qty":
                qty = random.randint(0, 15)  # 0 should trigger auto-removal
                cart.update_quantity(p_id, qty)

            elif action == "clear":
                if random.random() < 0.05:  # occasional clear
                    cart.clear()

            # Verify doubly linked list invariants after EVERY single mutation
            self.assertTrue(
                cart.verify_integrity(),
                f"Invariant broken at step {op_idx} during action '{action}' on item '{p_id}'"
            )

    def test_cart_two_node_swap_boundaries(self):
        """Specifically stress-test exactly 2 nodes swapping back and forth."""
        cart = DoublyLinkedListCart("two_nodes")
        cart.add_item("A", "Node A", 1, 10.0)
        cart.add_item("B", "Node B", 1, 20.0)

        # Move B up -> becomes [B, A]
        self.assertTrue(cart.move_item("B", "up"))
        self.assertEqual(cart.head.product_id, "B")
        self.assertEqual(cart.tail.product_id, "A")
        self.assertTrue(cart.verify_integrity())

        # Move B up again -> should fail (already head)
        self.assertFalse(cart.move_item("B", "up"))

        # Move A down -> should fail (already tail)
        self.assertFalse(cart.move_item("A", "down"))

        # Move B down -> becomes [A, B]
        self.assertTrue(cart.move_item("B", "down"))
        self.assertEqual(cart.head.product_id, "A")
        self.assertEqual(cart.tail.product_id, "B")
        self.assertTrue(cart.verify_integrity())

    def test_cart_negative_and_zero_inputs(self):
        """Ensure non-positive quantities on add_item raise ValueError."""
        cart = DoublyLinkedListCart("validation")
        with self.assertRaises(ValueError):
            cart.add_item("p1", "Item", 0, 10.0)
        with self.assertRaises(ValueError):
            cart.add_item("p2", "Item", -5, 10.0)

    # =========================================================================
    # 2. ORDER HISTORY & REORDERING EDGE CASES
    # =========================================================================

    def test_reorder_when_cart_already_contains_items(self):
        """
        If the cart already has an item with quantity 2, and we reorder an order
        that contains 3 of that same item, does the cart properly sum to 5?
        """
        cart = DoublyLinkedListCart("reorder_user")
        history = OrderHistoryList("reorder_user")

        # Create historical order with p1 (qty: 3)
        cart.add_item("p1", "Item 1", 3, 20.0)
        order = history.checkout(cart)
        self.assertEqual(cart.size, 0)

        # Now shopper adds p1 (qty: 2) to active cart
        cart.add_item("p1", "Item 1", 2, 20.0)
        self.assertEqual(cart.node_index["p1"].quantity, 2)

        # Shopper clicks Reorder
        success = history.reorder(order.order_id, cart)
        self.assertTrue(success)

        # Size should still be 1 (no duplicate node created) and quantity should be 5 (2 + 3)
        self.assertEqual(cart.size, 1)
        self.assertEqual(cart.node_index["p1"].quantity, 5)
        self.assertTrue(cart.verify_integrity())

    # =========================================================================
    # 3. RECOMMENDATION GRAPH EDGE CASES
    # =========================================================================

    def test_graph_isolated_and_self_loops(self):
        """Test self-loops are ignored and isolated nodes don't crash recommendation."""
        graph = ProductGraph()
        # Self-loop should be safely ignored
        graph.add_edge("p1", "p1", weight=1.0)
        self.assertEqual(len(graph.get_neighbors("p1")), 0)

        # Isolated node (has no neighbors)
        graph.add_node("p_isolated")
        recs = graph.recommend(seed_product_ids=["p_isolated"])
        self.assertEqual(len(recs), 0)

    def test_graph_all_neighbors_already_in_cart(self):
        """When all graph neighbors are already in the cart, recommendations should be empty (no duplicates)."""
        graph = ProductGraph()
        graph.add_edge("p1", "p2", weight=2.0)
        graph.add_edge("p1", "p3", weight=1.5)

        recs = graph.recommend(
            seed_product_ids=["p1"],
            exclude_product_ids={"p2", "p3"}
        )
        self.assertEqual(len(recs), 0)

    # =========================================================================
    # 4. REST API & SECURITY TESTING
    # =========================================================================

    def test_api_malformed_json_handling(self):
        """Test sending syntactically invalid JSON to POST /api/cart/items."""
        status, body = make_request("/api/cart/items", method="POST", body="{malformed json")
        # Should gracefully return 400 or handle without server crash
        self.assertIn(status, [400, 200])

    def test_api_missing_product_id(self):
        """Test sending payload without productId."""
        status, body = make_request("/api/cart/items", method="POST", body={"name": "Ghost", "quantity": 1})
        self.assertEqual(status, 400)
        self.assertFalse(body.get("success", False))

    def test_api_directory_traversal_attack(self):
        """
        SECURITY CHECK: Test directory traversal attempting to read sensitive
        files outside public/ folder (e.g. /../app.py or /../cart_storage.json).
        """
        status, _ = make_request("/../app.py", method="GET")
        # Must NOT return 200 (should be 404 or 403)
        self.assertNotEqual(status, 200, "SECURITY VULNERABILITY: Directory traversal succeeded!")

    def test_api_move_non_existent_item(self):
        """Moving an item not present in cart should return 400."""
        status, body = make_request("/api/cart/items/non_existent_id/move", method="POST", body={"direction": "up"})
        self.assertEqual(status, 400)
        self.assertFalse(body.get("success", True))

    def test_api_delete_non_existent_item(self):
        """Deleting an item not in cart should return 404."""
        status, body = make_request("/api/cart/items/non_existent_id", method="DELETE")
        self.assertEqual(status, 404)
        self.assertFalse(body.get("success", True))


if __name__ == "__main__":
    unittest.main()
