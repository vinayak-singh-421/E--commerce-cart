"""
Comprehensive Unit Tests for OrderHistoryList and Checkout Flow.
Verifies FR-8 to FR-12 as specified in PRD.md and TECHNICAL.md.
"""
import unittest
from cart_linked_list import DoublyLinkedListCart
from order_history import OrderHistoryList, OrderStatus


class TestOrderHistory(unittest.TestCase):

    def setUp(self):
        self.cart = DoublyLinkedListCart(user_id="user_test")
        self.history = OrderHistoryList(user_id="user_test")

    def test_checkout_empty_cart_raises_error(self):
        with self.assertRaises(ValueError):
            self.history.checkout(self.cart)

    def test_successful_checkout_creates_order_and_clears_cart(self):
        self.cart.add_item("prod_kb", "Mechanical Keyboard", 2, 100.0)
        self.cart.add_item("prod_mouse", "Wireless Mouse", 1, 50.0)
        self.assertEqual(self.cart.size, 2)

        order = self.history.checkout(self.cart)

        # 1. Verify Cart is cleared
        self.assertEqual(self.cart.size, 0)
        self.assertIsNone(self.cart.head)
        self.assertIsNone(self.cart.tail)
        self.assertEqual(len(self.cart.node_index), 0)

        # 2. Verify Order Node properties
        self.assertIsNotNone(order.order_id)
        self.assertEqual(order.status, OrderStatus.PLACED)
        self.assertEqual(len(order.items), 2)
        self.assertEqual(order.subtotal, 250.0)  # (2 * 100) + (1 * 50)
        self.assertEqual(order.tax, 20.0)       # 250 * 0.08
        self.assertEqual(order.total, 270.0)

        # 3. Verify OrderHistory head pointer
        self.assertEqual(self.history.count, 1)
        self.assertIs(self.history.head, order)

    def test_order_snapshot_is_immutable(self):
        """Changes to new cart items should never affect historical order snapshots."""
        self.cart.add_item("prod_kb", "Keyboard", 1, 100.0)
        order = self.history.checkout(self.cart)

        # Re-add same product with different quantity and price to cart
        self.cart.add_item("prod_kb", "Keyboard", 5, 200.0)

        # Historical order snapshot must remain unchanged
        self.assertEqual(order.items[0].quantity, 1)
        self.assertEqual(order.items[0].unit_price, 100.0)
        self.assertEqual(order.total, 108.0)

    def test_recency_ordering_prepends_to_head(self):
        """Newest orders should be at the head of the Singly Linked List (O(1))."""
        # Order 1
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        order1 = self.history.checkout(self.cart)

        # Order 2
        self.cart.add_item("p2", "Item 2", 1, 20.0)
        order2 = self.history.checkout(self.cart)

        # Order 3
        self.cart.add_item("p3", "Item 3", 1, 30.0)
        order3 = self.history.checkout(self.cart)

        self.assertEqual(self.history.count, 3)
        self.assertIs(self.history.head, order3)
        self.assertIs(order3.next, order2)
        self.assertIs(order2.next, order1)
        self.assertIsNone(order1.next)

        orders_list = self.history.get_orders()
        self.assertEqual([o["orderId"] for o in orders_list], [order3.order_id, order2.order_id, order1.order_id])

    def test_reorder_rehydrates_cart(self):
        """FR-11: Reorder should push all items from an order back into the cart linked list."""
        self.cart.add_item("p1", "Keyboard", 2, 80.0)
        self.cart.add_item("p2", "Mouse", 1, 40.0)
        order = self.history.checkout(self.cart)
        self.assertEqual(self.cart.size, 0)

        success = self.history.reorder(order.order_id, self.cart)
        self.assertTrue(success)

        # Cart should now contain both items with original quantities
        self.assertEqual(self.cart.size, 2)
        self.assertIn("p1", self.cart.node_index)
        self.assertIn("p2", self.cart.node_index)
        self.assertEqual(self.cart.node_index["p1"].quantity, 2)
        self.assertEqual(self.cart.node_index["p2"].quantity, 1)
        self.assertTrue(self.cart.verify_integrity())

    def test_update_order_status(self):
        """FR-12: Order status tracking."""
        self.cart.add_item("p1", "Item", 1, 20.0)
        order = self.history.checkout(self.cart)

        self.assertEqual(order.status, OrderStatus.PLACED)

        self.assertTrue(self.history.update_status(order.order_id, OrderStatus.PROCESSING))
        self.assertEqual(order.status, OrderStatus.PROCESSING)

        self.assertTrue(self.history.update_status(order.order_id, OrderStatus.SHIPPED))
        self.assertEqual(order.status, OrderStatus.SHIPPED)

        self.assertTrue(self.history.update_status(order.order_id, OrderStatus.DELIVERED))
        self.assertEqual(order.status, OrderStatus.DELIVERED)

        with self.assertRaises(ValueError):
            self.history.update_status(order.order_id, "INVALID_STATUS")

    def test_serialization_round_trip(self):
        self.cart.add_item("p1", "Item 1", 1, 15.0)
        self.history.checkout(self.cart)
        self.cart.add_item("p2", "Item 2", 3, 25.0)
        self.history.checkout(self.cart)

        serialized = self.history.to_list()
        restored = OrderHistoryList.from_list(serialized, user_id="user_test")

        self.assertEqual(restored.count, 2)
        restored_orders = restored.get_orders()
        self.assertEqual(len(restored_orders), 2)
        self.assertEqual(restored_orders[0]["orderId"], serialized[0]["orderId"])
        self.assertEqual(restored_orders[1]["orderId"], serialized[1]["orderId"])


if __name__ == "__main__":
    unittest.main()
