from typing import TypeAlias

Product: TypeAlias = dict[str, int | str | float]


products: dict[int, Product] = {
    101: {
        "id": 101,
        "name": "Keyboard",
        "sku": "KEY-101",
        "category": "electronics",
        "price": 2500.0,
    },
    102: {
        "id": 102,
        "name": "Desk",
        "sku": "DESK-102",
        "category": "furniture",
        "price": 8000.0,
    },
}


class ProductRepository:
    def __init__(self, initial_products: dict[int, Product] | None = None) -> None:
        self.products = initial_products if initial_products is not None else {
            product_id: product.copy()
            for product_id, product in products.items()
        }
        self.next_id = max(self.products, default=100) + 1

    def get_product(self, product_id: int) -> Product | None:
        return self.products.get(product_id)

    def find_product_by_sku(self, sku: str) -> Product | None:
        return next(
            (product for product in self.products.values() if product["sku"] == sku),
            None,
        )

    def list_products(self) -> list[Product]:
        return list(self.products.values())

    def add_product(
        self,
        name: str,
        sku: str,
        category: str,
        price: float,
    ) -> Product:
        product: Product = {
            "id": self.next_id,
            "name": name,
            "sku": sku,
            "category": category,
            "price": price,
        }
        self.products[self.next_id] = product
        self.next_id += 1
        return product