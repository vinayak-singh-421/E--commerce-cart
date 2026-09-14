"""
Comprehensive Unit Tests for DoublyLinkedListCart.
Verifies all operations and invariants defined in PRD.md and TECHNICAL.md.
"""
import unittest
from cart_linked_list import DoublyLinkedListCart, CartItemNode


class TestDoublyLinkedListCart(unittest.TestCase):

    def setUp(self):
        self.cart = DoublyLinkedListCart(user_id="user_123")

    def test_initial_state(self):
        self.assertEqual(self.cart.size, 0)
        self.assertIsNone(self.cart.head)
        self.assertIsNone(self.cart.tail)
        self.assertEqual(len(self.cart.node_index), 0)
        self.assertTrue(self.cart.verify_integrity())

    def test_add_single_item(self):
        node = self.cart.add_item("prod_1", "Mechanical Keyboard", 1, 99.99)
        self.assertEqual(self.cart.size, 1)
        self.assertIs(self.cart.head, node)
        self.assertIs(self.cart.tail, node)
        self.assertIsNone(node.prev)
        self.assertIsNone(node.next)
        self.assertIn("prod_1", self.cart.node_index)
        self.assertIs(self.cart.node_index["prod_1"], node)
        self.assertTrue(self.cart.verify_integrity())

    def test_add_multiple_items_preserves_order(self):
        n1 = self.cart.add_item("p1", "Item 1", 1, 10.0)
        n2 = self.cart.add_item("p2", "Item 2", 2, 20.0)
        n3 = self.cart.add_item("p3", "Item 3", 1, 30.0)

        self.assertEqual(self.cart.size, 3)
        self.assertIs(self.cart.head, n1)
        self.assertIs(self.cart.tail, n3)

        # Verify pointer connections
        self.assertIsNone(n1.prev)
        self.assertIs(n1.next, n2)
        self.assertIs(n2.prev, n1)
        self.assertIs(n2.next, n3)
        self.assertIs(n3.prev, n2)
        self.assertIsNone(n3.next)

        traversed_ids = [item.product_id for item in self.cart.traverse()]
        self.assertEqual(traversed_ids, ["p1", "p2", "p3"])
        self.assertTrue(self.cart.verify_integrity())

    def test_add_existing_item_updates_quantity(self):
        self.cart.add_item("p1", "Item 1", 1, 15.0)
        self.cart.add_item("p2", "Item 2", 1, 25.0)
        self.assertEqual(self.cart.size, 2)

        # Add more of p1
        node = self.cart.add_item("p1", "Item 1", 3, 15.0)
        self.assertEqual(self.cart.size, 2)
        self.assertEqual(node.quantity, 4)
        self.assertEqual(self.cart.node_index["p1"].quantity, 4)
        self.assertTrue(self.cart.verify_integrity())

    def test_remove_single_item(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        success = self.cart.remove_item("p1")
        self.assertTrue(success)
        self.assertEqual(self.cart.size, 0)
        self.assertIsNone(self.cart.head)
        self.assertIsNone(self.cart.tail)
        self.assertNotIn("p1", self.cart.node_index)
        self.assertTrue(self.cart.verify_integrity())

    def test_remove_non_existent_item(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        success = self.cart.remove_item("ghost_id")
        self.assertFalse(success)
        self.assertEqual(self.cart.size, 1)

    def test_remove_head_node(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        self.cart.add_item("p2", "Item 2", 1, 20.0)
        self.cart.add_item("p3", "Item 3", 1, 30.0)

        # Remove head (p1)
        success = self.cart.remove_item("p1")
        self.assertTrue(success)
        self.assertEqual(self.cart.size, 2)
        self.assertEqual(self.cart.head.product_id, "p2")
        self.assertIsNone(self.cart.head.prev)
        self.assertIs(self.cart.head.next, self.cart.tail)
        self.assertEqual([item.product_id for item in self.cart.traverse()], ["p2", "p3"])
        self.assertTrue(self.cart.verify_integrity())

    def test_remove_tail_node(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        self.cart.add_item("p2", "Item 2", 1, 20.0)
        self.cart.add_item("p3", "Item 3", 1, 30.0)

        # Remove tail (p3)
        success = self.cart.remove_item("p3")
        self.assertTrue(success)
        self.assertEqual(self.cart.size, 2)
        self.assertEqual(self.cart.tail.product_id, "p2")
        self.assertIsNone(self.cart.tail.next)
        self.assertIs(self.cart.head, self.cart.tail.prev)
        self.assertEqual([item.product_id for item in self.cart.traverse()], ["p1", "p2"])
        self.assertTrue(self.cart.verify_integrity())

    def test_remove_middle_node(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        self.cart.add_item("p2", "Item 2", 1, 20.0)
        self.cart.add_item("p3", "Item 3", 1, 30.0)

        # Remove middle (p2)
        success = self.cart.remove_item("p2")
        self.assertTrue(success)
        self.assertEqual(self.cart.size, 2)
        self.assertEqual(self.cart.head.product_id, "p1")
        self.assertEqual(self.cart.tail.product_id, "p3")
        self.assertIs(self.cart.head.next, self.cart.tail)
        self.assertIs(self.cart.tail.prev, self.cart.head)
        self.assertEqual([item.product_id for item in self.cart.traverse()], ["p1", "p3"])
        self.assertTrue(self.cart.verify_integrity())

    def test_update_quantity(self):
        self.cart.add_item("p1", "Item 1", 2, 15.0)
        self.cart.update_quantity("p1", 5)
        self.assertEqual(self.cart.node_index["p1"].quantity, 5)

        # Update with quantity <= 0 should remove the item
        self.cart.update_quantity("p1", 0)
        self.assertEqual(self.cart.size, 0)
        self.assertNotIn("p1", self.cart.node_index)
        self.assertTrue(self.cart.verify_integrity())

    def test_move_item_up_and_down(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        self.cart.add_item("p2", "Item 2", 1, 20.0)
        self.cart.add_item("p3", "Item 3", 1, 30.0)

        # Moving head up should fail (already top)
        self.assertFalse(self.cart.move_item("p1", "up"))

        # Moving tail down should fail (already bottom)
        self.assertFalse(self.cart.move_item("p3", "down"))

        # Move p2 up -> order should become [p2, p1, p3]
        self.assertTrue(self.cart.move_item("p2", "up"))
        self.assertEqual([i.product_id for i in self.cart.traverse()], ["p2", "p1", "p3"])
        self.assertEqual(self.cart.head.product_id, "p2")
        self.assertTrue(self.cart.verify_integrity())

        # Move p2 down -> order returns to [p1, p2, p3]
        self.assertTrue(self.cart.move_item("p2", "down"))
        self.assertEqual([i.product_id for i in self.cart.traverse()], ["p1", "p2", "p3"])
        self.assertEqual(self.cart.head.product_id, "p1")
        self.assertTrue(self.cart.verify_integrity())

        # Move p3 up -> order becomes [p1, p3, p2]
        self.assertTrue(self.cart.move_item("p3", "up"))
        self.assertEqual([i.product_id for i in self.cart.traverse()], ["p1", "p3", "p2"])
        self.assertEqual(self.cart.tail.product_id, "p2")
        self.assertTrue(self.cart.verify_integrity())

    def test_reverse_traversal(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        self.cart.add_item("p2", "Item 2", 1, 20.0)
        self.cart.add_item("p3", "Item 3", 1, 30.0)

        reverse_ids = [item.product_id for item in self.cart.traverse(reverse=True)]
        self.assertEqual(reverse_ids, ["p3", "p2", "p1"])

    def test_totals_and_summary(self):
        self.cart.add_item("p1", "Item 1", 2, 50.0)  # subtotal = 100.0
        self.cart.add_item("p2", "Item 2", 1, 50.0)  # subtotal = 50.0

        summary = self.cart.get_summary(tax_rate=0.08)
        self.assertEqual(summary["size"], 2)
        self.assertEqual(summary["totalQuantity"], 3)
        self.assertEqual(summary["subtotal"], 150.0)
        self.assertEqual(summary["taxEstimate"], 12.0)  # 150 * 0.08 = 12.0
        self.assertEqual(summary["total"], 162.0)

    def test_clear_cart(self):
        self.cart.add_item("p1", "Item 1", 1, 10.0)
        self.cart.add_item("p2", "Item 2", 1, 20.0)
        self.cart.clear()

        self.assertEqual(self.cart.size, 0)
        self.assertIsNone(self.cart.head)
        self.assertIsNone(self.cart.tail)
        self.assertEqual(len(self.cart.node_index), 0)
        self.assertTrue(self.cart.verify_integrity())

    def test_serialization_round_trip(self):
        self.cart.add_item("p1", "Item 1", 2, 29.99)
        self.cart.add_item("p2", "Item 2", 1, 49.99)

        data = self.cart.to_dict()
        restored = DoublyLinkedListCart.from_dict(data)

        self.assertEqual(restored.size, 2)
        self.assertEqual([i.product_id for i in restored.traverse()], ["p1", "p2"])
        self.assertEqual(restored.node_index["p1"].quantity, 2)
        self.assertTrue(restored.verify_integrity())


if __name__ == "__main__":
    unittest.main()
