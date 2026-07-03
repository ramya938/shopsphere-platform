import uuid
from fastapi import APIRouter, Depends, status
from src.api.schemas.cart import CartResponse, CartItemAdd, CartItemUpdate
from src.services.cart_service import CartService
from src.api.deps import get_cart_service, get_current_user_claims

router = APIRouter()

@router.get(
    "/",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active shopping cart",
    description="Fetches the current user's active shopping cart and its list of items."
)
async def get_cart(
    cart_service: CartService = Depends(get_cart_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    return await cart_service.get_or_create_cart(user_id)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Add product item to cart",
    description="Adds a product item to the user's active cart. Checks stock levels with the Product Service catalog first."
)
async def add_item(
    request: CartItemAdd,
    cart_service: CartService = Depends(get_cart_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    return await cart_service.add_item_to_cart(
        user_id=user_id,
        product_id=request.product_id,
        quantity=request.quantity
    )


@router.put(
    "/items/{product_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product item quantity",
    description="Updates the quantity of a product item inside the user's active cart. Set quantity to 0 to remove."
)
async def update_item(
    product_id: uuid.UUID,
    request: CartItemUpdate,
    cart_service: CartService = Depends(get_cart_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    return await cart_service.update_item_quantity(
        user_id=user_id,
        product_id=product_id,
        quantity=request.quantity
    )


@router.delete(
    "/items/{product_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove product item from cart",
    description="Removes a product item entirely from the user's active shopping cart."
)
async def remove_item(
    product_id: uuid.UUID,
    cart_service: CartService = Depends(get_cart_service),
    claims: dict = Depends(get_current_user_claims)
):
    user_id = uuid.UUID(claims.get("sub"))
    return await cart_service.remove_item_from_cart(user_id=user_id, product_id=product_id)
