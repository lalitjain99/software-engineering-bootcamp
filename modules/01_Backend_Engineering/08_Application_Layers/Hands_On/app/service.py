from app.exceptions import DuplicateSkuError, ProductNotFoundError
from app.repository import ProductRepository


class ProductService:
    def __init__(self, product_repository: ProductRepository) -> None:
        self.product_repository = product_repository

    def create_product(
        self,
        name: str,
        sku: str,
        category: str,
        price: float,
    ) -> dict[str, object]:
        normalized_name = name.strip()
        normalized_sku = sku.strip().upper()
        normalized_category = category.strip().lower()

        if self.product_repository.find_product_by_sku(normalized_sku) is not None:
            raise DuplicateSkuError(
                f"Product with SKU {normalized_sku} already exists"
            )

        return self.product_repository.add_product(
            name=normalized_name,
            sku=normalized_sku,
            category=normalized_category,
            price=price,
        )

    def get_product(self, product_id: int) -> dict[str, object]:
        product = self.product_repository.get_product(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} was not found")
        return product

    def list_products(
        self,
        category: str | None = None,
    ) -> list[dict[str, object]]:
        products = self.product_repository.list_products()
        if category is None:
            return products

        normalized_category = category.strip().lower()
        return [
            product
            for product in products
            if product["category"] == normalized_category
        ]
    
