from app.repository import ProductRepository

class ProductService:
    def __init__(self):
        self.product_repository = ProductRepository