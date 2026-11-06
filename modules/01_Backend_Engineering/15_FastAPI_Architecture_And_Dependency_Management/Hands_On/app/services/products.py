from app.repositories import ProductRepository

class ProductNotFoundError(Exception):
    def __init__(self, product_id, message):
        self.product_id = product_id
        self.message = message or f"Product with ID {product_id} was not found"
        super().__init__(self.message)



class ProductService:

    def __init__(self):
        self.product_repository = ProductRepository


    def get_product(self,product_id):
        
        product = self.product_repository.find_product(product_id)

        if not product:
            raise ProductNotFoundError(product_id)
        return product
        

        

