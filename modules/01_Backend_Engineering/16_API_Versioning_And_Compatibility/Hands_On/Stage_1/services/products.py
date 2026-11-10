from repositories.products import ProductRepository

class ProductNotFoundError(Exception):
    def __init__(self, product_id):
        self.message = f"Product with product id {product_id} not found"
        super().__init__(self.message)


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def get_product(self,product_id: int):
        product = self.repository.get_product(product_id)

        if product is None:
            raise ProductNotFoundError
        return product