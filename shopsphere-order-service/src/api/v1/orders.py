import uuid
from typing import Sequence
from fastapi import APIRouter, Depends, status, Query
from src.api.schemas.order import OrderResponse, DirectOrderCreate, CartCheckout, OrderStatusUpdate
from src.services.order_service import OrderService
from src.api.deps import get_order_service, get_current_user_claims, RoleChecker

router = APIRouter()

@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout shopping cart",
    description="Creates an order from all active items inside the user's shopping cart, reserves stock levels, and clears the cart."
)
async def checkout(
    request: CartCheckout,
    order_service: OrderService = Depends(get_order_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    return await order_service.checkout_cart(
        user_id=user_id,
        shipping_address=request.shipping_address
    )


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a direct order",
    description="Directly checkout list of items bypassing the shopping cart. Checks stock levels and creates order in CREATED status."
)
async def place_order(
    request: DirectOrderCreate,
    order_service: OrderService = Depends(get_order_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    # Map pydantic OrderItemRequest models to list of dicts
    items = [{"product_id": item.product_id, "quantity": item.quantity} for item in request.items]
    return await order_service.place_direct_order(
        user_id=user_id,
        items=items,
        shipping_address=request.shipping_address
    )


@router.get(
    "/me",
    response_model=list[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my order history",
    description="Retrieves a list of all orders placed by the current customer, ordered by newest creation date."
)
async def list_my_orders(
    order_service: OrderService = Depends(get_order_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    return await order_service.list_my_orders(user_id)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get order details",
    description="Retrieves structural details for a specific order. Accessible by the order owner or administrative accounts."
)
async def get_order(
    order_id: uuid.UUID,
    order_service: OrderService = Depends(get_order_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    role = claims.get("role")
    return await order_service.get_order(order_id=order_id, user_id=user_id, user_role=role)


@router.get(
    "/",
    response_model=list[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List all orders",
    description="Retrieves a list of all orders placed in the system. Restricted to administrative accounts."
)
async def list_all_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    order_service: OrderService = Depends(get_order_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    return await order_service.list_all_orders(skip=skip, limit=limit)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Transition order status",
    description="Transitions an order status. Admins can change to any valid state; customers can only cancel their own orders."
)
async def update_status(
    order_id: uuid.UUID,
    request: OrderStatusUpdate,
    order_service: OrderService = Depends(get_order_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    role = claims.get("role")
    return await order_service.transition_status(
        order_id=order_id,
        user_id=user_id,
        user_role=role,
        new_status=request.status
    )
