from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.domain.models import Cart, Order

class CartRepositoryInterface(ABC):
    """Abstract interface for Cart persistence operations."""

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> Cart | None:
        """Retrieve a user's active shopping cart, including its items."""
        pass

    @abstractmethod
    async def add(self, cart: Cart) -> Cart:
        """Add a new shopping cart."""
        pass

    @abstractmethod
    async def update(self, cart: Cart) -> Cart:
        """Update a shopping cart's items or details."""
        pass

    @abstractmethod
    async def delete(self, cart: Cart) -> None:
        """Delete a shopping cart."""
        pass


class OrderRepositoryInterface(ABC):
    """Abstract interface for Order persistence operations."""

    @abstractmethod
    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Retrieve an order by its UUID, including items."""
        pass

    @abstractmethod
    async def add(self, order: Order) -> Order:
        """Add a new order to database."""
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """Update an existing order."""
        pass

    @abstractmethod
    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[Order]:
        """Retrieve all orders placed by a specific user, ordered by creation date desc."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Order]:
        """Retrieve all orders, ordered by creation date desc."""
        pass
