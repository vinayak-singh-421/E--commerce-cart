"""
Order History & Checkout System using an Append-Only (Recency) Singly Linked List.
Follows requirements in PRD.md (FR-8 to FR-12) and TECHNICAL.md (Section 3.2).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from cart_linked_list import DoublyLinkedListCart


class OrderStatus:
    PLACED = "PLACED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

    ALL = [PLACED, PROCESSING, SHIPPED, DELIVERED, CANCELLED]


class OrderItem:
    """
    Immutable snapshot of a purchased item at checkout time.
    Separated completely from live cart nodes.
    """
    def __init__(self, product_id: str, name: str, quantity: int, unit_price: float):
        self.product_id: str = product_id
        self.name: str = name
        self.quantity: int = int(quantity)
        self.unit_price: float = float(unit_price)
        self.total_price: float = round(self.quantity * self.unit_price, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "productId": self.product_id,
            "name": self.name,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "totalPrice": self.total_price
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        return cls(
            product_id=data["productId"],
            name=data["name"],
            quantity=data["quantity"],
            unit_price=data["unitPrice"]
        )


class OrderNode:
    """
    Node in the Singly Linked List of Orders.
    Points to the next older order (head = newest order).
    """
    def __init__(
        self,
        order_id: str,
        user_id: str,
        items: List[OrderItem],
        subtotal: float,
        tax: float,
        total: float,
        status: str = OrderStatus.PLACED,
        created_at: Optional[str] = None
    ):
        self.order_id: str = order_id
        self.user_id: str = user_id
        self.items: List[OrderItem] = items
        self.subtotal: float = float(subtotal)
        self.tax: float = float(tax)
        self.total: float = float(total)
        self.status: str = status if status in OrderStatus.ALL else OrderStatus.PLACED
        self.created_at: str = created_at or datetime.now(timezone.utc).isoformat()
        self.next: Optional['OrderNode'] = None  # Points to next-older order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "orderId": self.order_id,
            "userId": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "itemCount": len(self.items),
            "totalQuantity": sum(item.quantity for item in self.items),
            "subtotal": self.subtotal,
            "tax": self.tax,
            "total": self.total,
            "status": self.status,
            "createdAt": self.created_at,
            "nextOrderId": self.next.order_id if self.next else None
        }


class OrderHistoryList:
    """
    Singly Linked List of Orders ordered by recency.
    Newest orders are prepended to the head in O(1) time.
    """
    def __init__(self, user_id: str = "default_user"):
        self.user_id: str = user_id
        self.head: Optional[OrderNode] = None
        self.count: int = 0

    def checkout(self, cart: DoublyLinkedListCart) -> OrderNode:
        """
        Checkout Flow:
        1. Validates cart is non-empty.
        2. Traverses Cart Linked List once (O(n)) to build immutable OrderItem snapshot.
        3. Prepends new OrderNode to head of order history in O(1).
        4. Clears active cart (O(1)).
        """
        if cart.size == 0:
            raise ValueError("Cannot checkout an empty cart")

        summary = cart.get_summary()

        # Build immutable snapshot copies of all cart items
        snapshot_items: List[OrderItem] = []
        for item_data in summary["items"]:
            snapshot_items.append(OrderItem(
                product_id=item_data["productId"],
                name=item_data["name"],
                quantity=item_data["quantity"],
                unit_price=item_data["unitPrice"]
            ))

        # Generate human-readable order ID with timestamp
        short_id = uuid.uuid4().hex[:6].upper()
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{short_id}"

        new_order = OrderNode(
            order_id=order_id,
            user_id=self.user_id,
            items=snapshot_items,
            subtotal=summary["subtotal"],
            tax=summary["taxEstimate"],
            total=summary["total"],
            status=OrderStatus.PLACED
        )

        # Prepend to head (O(1) insertion)
        new_order.next = self.head
        self.head = new_order
        self.count += 1

        # Clear the active shopping cart
        cart.clear()

        return new_order

    def get_orders(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Traverses order history from newest to oldest.
        """
        orders = []
        current = self.head
        while current is not None and (limit is None or len(orders) < limit):
            orders.append(current.to_dict())
            current = current.next
        return orders

    def get_order_node(self, order_id: str) -> Optional[OrderNode]:
        current = self.head
        while current is not None:
            if current.order_id == order_id:
                return current
            current = current.next
        return None

    def reorder(self, order_id: str, cart: DoublyLinkedListCart) -> bool:
        """
        FR-11: Re-add all items from a past order back into the cart linked list.
        """
        order_node = self.get_order_node(order_id)
        if not order_node:
            return False

        for item in order_node.items:
            cart.add_item(
                product_id=item.product_id,
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price
            )
        return True

    def update_status(self, order_id: str, new_status: str) -> bool:
        """
        FR-12: Update order tracking status (Placed -> Processing -> Shipped -> Delivered).
        """
        new_status = str(new_status or "").strip().upper()
        if new_status not in OrderStatus.ALL:
            raise ValueError(f"Invalid status: '{new_status}'. Allowed: {OrderStatus.ALL}")

        order_node = self.get_order_node(order_id)
        if not order_node:
            return False

        order_node.status = new_status
        return True

    def to_list(self) -> List[Dict[str, Any]]:
        return self.get_orders()

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]], user_id: str = "default_user") -> 'OrderHistoryList':
        """
        Reconstructs the singly linked list from serialized data (ordered newest to oldest).
        """
        history = cls(user_id=user_id)
        # Reconstruct by prepending in reverse (oldest first, so newest ends up at head)
        for order_data in reversed(data):
            items = [OrderItem.from_dict(it) for it in order_data["items"]]
            node = OrderNode(
                order_id=order_data["orderId"],
                user_id=order_data.get("userId", user_id),
                items=items,
                subtotal=order_data["subtotal"],
                tax=order_data["tax"],
                total=order_data["total"],
                status=order_data.get("status", OrderStatus.PLACED),
                created_at=order_data.get("createdAt")
            )
            node.next = history.head
            history.head = node
            history.count += 1
        return history
