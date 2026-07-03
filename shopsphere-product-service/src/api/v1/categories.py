import uuid
from fastapi import APIRouter, Depends, status
from src.api.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from src.services.category_service import CategoryService
from src.api.deps import get_category_service, RoleChecker

router = APIRouter()

@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Creates a product classification category. Restricted to ADMIN users only."
)
async def create_category(
    request: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    return await category_service.create_category(
        name=request.name,
        description=request.description
    )


@router.get(
    "/",
    response_model=list[CategoryResponse],
    summary="List all categories",
    description="Retrieves a list of all categories. Public access."
)
async def list_categories(
    category_service: CategoryService = Depends(get_category_service)
):
    return await category_service.list_categories()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category details",
    description="Retrieves category metadata by UUID. Public access."
)
async def get_category(
    category_id: uuid.UUID,
    category_service: CategoryService = Depends(get_category_service)
):
    return await category_service.get_category(category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category details",
    description="Updates category name or description. Restricted to ADMIN users only."
)
async def update_category(
    category_id: uuid.UUID,
    request: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    return await category_service.update_category(
        category_id=category_id,
        name=request.name,
        description=request.description
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    description="Permanently deletes a category by UUID. Restricted to ADMIN users only."
)
async def delete_category(
    category_id: uuid.UUID,
    category_service: CategoryService = Depends(get_category_service),
    _admin_auth: dict = Depends(RoleChecker(["ADMIN"]))
):
    await category_service.delete_category(category_id)
