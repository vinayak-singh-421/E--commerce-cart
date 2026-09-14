"""
Doubly Linked List Cart implementation with O(1) Hash Map Index.
Follows requirements in PRD.md, TECHNICAL.md, and ARCHITECTURE.md.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


class CartItemNode:
    """
    A single node in the Doubly Linked List Cart.
    Holds product details and pointers to previous and next items.
    """
    def __init__(self, product_id: str, name: str, quantity: int, unit_price: float, added_at: Optional[str] = None):
        self.product_id: str = product_id
        self.name: str = name
        self.quantity: int = int(quantity)
        self.unit_price: float = float(unit_price)
        self.added_at: str = added_at or datetime.now(timezone.utc).isoformat()
        self.prev: Optional['CartItemNode'] = None
        self.next: Optional['CartItemNode'] = None

    @property
    def total_price(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "productId": self.product_id,
            "name": self.name,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "totalPrice": self.total_price,
            "addedAt": self.added_at,
            "hasPrev": self.prev is not None,
            "hasNext": self.next is not None,
            "prevProductId": self.prev.product_id if self.prev else None,
            "nextProductId": self.next.product_id if self.next else None,
        }


class DoublyLinkedListCart:
    """
    Doubly Linked List Cart with a supporting hash index (node_index).
    - Preserves sequential ordering of items.
    - O(1) appending, deletion, and adjacent swapping.
    - O(1) lookup via node_index dictionary.
    """
    def __init__(self, user_id: str = "default_user"):
        self.user_id: str = user_id
        self.head: Optional[CartItemNode] = None
        self.tail: Optional[CartItemNode] = None
        self.size: int = 0
        self.node_index: Dict[str, CartItemNode] = {}

    def add_item(self, product_id: str, name: str, quantity: int, unit_price: float) -> CartItemNode:
        """
        O(1) operation:
        If product already in cart, update quantity.
        Otherwise, append a new CartItemNode to the tail of the linked list.
        """
        quantity = int(quantity)
        unit_price = float(unit_price)

        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")

        # Fast O(1) check using the hash map index
        if product_id in self.node_index:
            existing_node = self.node_index[product_id]
            existing_node.quantity += quantity
            return existing_node

        new_node = CartItemNode(product_id, name, quantity, unit_price)

        if self.head is None:
            # First item in cart
            self.head = new_node
            self.tail = new_node
        else:
            # Append to tail
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node

        self.size += 1
        self.node_index[product_id] = new_node
        return new_node

    def remove_item(self, product_id: str) -> bool:
        """
        O(1) operation:
        Locate node via node_index, unlink its pointers, and delete from index.
        """
        if product_id not in self.node_index:
            return False

        node = self.node_index[product_id]

        if node == self.head and node == self.tail:
            # Single item in cart
            self.head = None
            self.tail = None
        elif node == self.head:
            # Removing head
            self.head = node.next
            self.head.prev = None
        elif node == self.tail:
            # Removing tail
            self.tail = node.prev
            self.tail.next = None
        else:
            # Removing middle node
            node.prev.next = node.next
            node.next.prev = node.prev

        # Unlink removed node
        node.prev = None
        node.next = None

        del self.node_index[product_id]
        self.size -= 1
        return True

    def update_quantity(self, product_id: str, quantity: int) -> bool:
        """
        O(1) operation:
        Update quantity of an existing item. If quantity <= 0, remove the item.
        """
        if product_id not in self.node_index:
            return False

        quantity = int(quantity)
        if quantity <= 0:
            return self.remove_item(product_id)

        node = self.node_index[product_id]
        node.quantity = quantity
        return True

    def move_item(self, product_id: str, direction: str) -> bool:
        """
        O(1) operation:
        Swaps an item with its immediate neighbor ('up' toward head, or 'down' toward tail).
        """
        if product_id not in self.node_index:
            return False

        node = self.node_index[product_id]

        direction = direction.lower()
        if direction in ("up", "prev"):
            # Move towards head (swap with node.prev)
            if node.prev is None:
                return False  # Already at head
            self._swap_adjacent(node.prev, node)
            return True
        elif direction in ("down", "next"):
            # Move towards tail (swap with node.next)
            if node.next is None:
                return False  # Already at tail
            self._swap_adjacent(node, node.next)
            return True
        else:
            raise ValueError(f"Unknown direction: {direction}. Use 'up' or 'down'.")

    def _swap_adjacent(self, node_a: CartItemNode, node_b: CartItemNode) -> None:
        """
        Helper to swap adjacent nodes: ... <-> A <-> B <-> ...
        Becomes: ... <-> B <-> A <-> ...
        """
        assert node_a.next == node_b and node_b.prev == node_a, "Nodes must be strictly adjacent (A -> B)"

        prev_node = node_a.prev
        next_node = node_b.next

        # Link outer nodes
        if prev_node is not None:
            prev_node.next = node_b
        else:
            self.head = node_b
        node_b.prev = prev_node

        if next_node is not None:
            next_node.prev = node_a
        else:
            self.tail = node_a
        node_a.next = next_node

        # Link B and A together
        node_b.next = node_a
        node_a.prev = node_b

    def traverse(self, reverse: bool = False) -> List[CartItemNode]:
        """
        O(n) traversal from head to tail (or tail to head if reverse is True).
        """
        items = []
        if not reverse:
            current = self.head
            while current is not None:
                items.append(current)
                current = current.next
        else:
            current = self.tail
            while current is not None:
                items.append(current)
                current = current.prev
        return items

    def get_summary(self, tax_rate: float = 0.08) -> Dict[str, Any]:
        """
        Calculates running subtotal, tax estimate, and total.
        """
        items_list = []
        subtotal = 0.0
        total_quantity = 0

        current = self.head
        position = 0
        while current is not None:
            subtotal += current.total_price
            total_quantity += current.quantity
            item_data = current.to_dict()
            item_data["position"] = position
            items_list.append(item_data)
            current = current.next
            position += 1

        subtotal = round(subtotal, 2)
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)

        return {
            "userId": self.user_id,
            "size": self.size,
            "totalQuantity": total_quantity,
            "subtotal": subtotal,
            "taxEstimate": tax,
            "total": total,
            "items": items_list,
            "headProductId": self.head.product_id if self.head else None,
            "tailProductId": self.tail.product_id if self.tail else None,
            "nodeIndexKeys": list(self.node_index.keys()),
        }

    def clear(self) -> None:
        """
        O(1) operation:
        Unlink head, tail, and clear hash index.
        """
        self.head = None
        self.tail = None
        self.size = 0
        self.node_index.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "userId": self.user_id,
            "items": [
                {
                    "productId": item.product_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unitPrice": item.unit_price,
                    "addedAt": item.added_at
                }
                for item in self.traverse()
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DoublyLinkedListCart':
        cart = cls(user_id=data.get("userId", "default_user"))
        for item in data.get("items", []):
            node = cart.add_item(
                product_id=item["productId"],
                name=item["name"],
                quantity=item["quantity"],
                unit_price=item["unitPrice"]
            )
            if "addedAt" in item:
                node.added_at = item["addedAt"]
        return cart

    def verify_integrity(self) -> bool:
        """
        Sanity check for linked list invariants:
        - size matches count of items traversed
        - size matches len(node_index)
        - head.prev is None, tail.next is None
        - for every node: node.next.prev == node and node.prev.next == node
        - every node exists in node_index
        """
        if self.size == 0:
            return self.head is None and self.tail is None and len(self.node_index) == 0

        if self.head is None or self.tail is None:
            return False

        if self.head.prev is not None or self.tail.next is not None:
            return False

        current = self.head
        count = 0
        prev_node = None

        while current is not None:
            count += 1
            if current.prev != prev_node:
                return False
            if current.product_id not in self.node_index:
                return False
            if self.node_index[current.product_id] is not current:
                return False

            prev_node = current
            current = current.next

        if count != self.size or count != len(self.node_index):
            return False

        if prev_node != self.tail:
            return False

        return True
