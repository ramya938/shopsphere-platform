import uuid
from fastapi import APIRouter, Depends, Query, status
from src.api.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, InventoryUpdate
from src.services.product_service import ProductService
from src.api.deps import get_product_service, RoleChecker
from src.domain.models import ProductStatus

router = APIRouter()

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Creates a product with inventory records. Restricted to ADMIN users only."
)
async def create_product(
    request: ProductCreate,
    product_service: ProductService = Depends(get_product_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    return await product_service.create_product(
        name=request.name,
        price=request.price,
        inventory_quantity=request.inventory_quantity,
        description=request.description,
        image_url=request.image_url,
        status=request.status,
        category_id=request.category_id
    )


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="Search and list products",
    description="Query, filter, sort, and paginate active catalog products. Public access."
)
async def list_products(
    search: str | None = Query(default=None, description="Search keyword in name or description"),
    category_id: uuid.UUID | None = Query(default=None, description="Filter by category UUID"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price limit"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price limit"),
    status: ProductStatus | None = Query(default=None, description="Filter by status (DRAFT, ACTIVE, OUT_OF_STOCK)"),
    sort_by: str | None = Query(default="created_at", description="Field to sort by (price, created_at, name)"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort direction (asc or desc)"),
    skip: int = Query(default=0, ge=0, description="Skipped results offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum items per page"),
    product_service: ProductService = Depends(get_product_service)
):
    products, total_count = await product_service.list_products(
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )
    return ProductListResponse(
        total_count=total_count,
        products=products,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product details",
    description="Retrieves category metadata by UUID. Public access."
)
async def get_product(
    product_id: uuid.UUID,
    product_service: ProductService = Depends(get_product_service)
):
    return await product_service.get_product(product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details",
    description="Updates product specifications and price. Restricted to ADMIN users only."
)
async def update_product(
    product_id: uuid.UUID,
    request: ProductUpdate,
    product_service: ProductService = Depends(get_product_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    return await product_service.update_product(
        product_id=product_id,
        name=request.name,
        price=request.price,
        inventory_quantity=request.inventory_quantity,
        description=request.description,
        image_url=request.image_url,
        status=request.status,
        category_id=request.category_id
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    description="Permanently deletes a product. Restricted to ADMIN users only."
)
async def delete_product(
    product_id: uuid.UUID,
    product_service: ProductService = Depends(get_product_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    await product_service.delete_product(product_id)


@router.post(
    "/{product_id}/deduct",
    response_model=ProductResponse,
    summary="Deduct product inventory",
    description="Reduces product stock levels after checkout. Restricted to ADMIN or internal service tokens."
)
async def deduct_inventory(
    product_id: uuid.UUID,
    request: InventoryUpdate,
    product_service: ProductService = Depends(get_product_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    return await product_service.deduct_inventory(product_id, request.quantity)


@router.post(
    "/{product_id}/restock",
    response_model=ProductResponse,
    summary="Restock product inventory",
    description="Restock product inventory levels. Restricted to ADMIN users only."
)
async def add_inventory(
    product_id: uuid.UUID,
    request: InventoryUpdate,
    product_service: ProductService = Depends(get_product_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    return await product_service.add_inventory(product_id, request.quantity)
