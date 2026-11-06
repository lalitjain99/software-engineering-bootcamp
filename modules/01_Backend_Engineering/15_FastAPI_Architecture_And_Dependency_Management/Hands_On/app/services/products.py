from app.repositories.products import ProductRepository

class ProductNotFoundError(Exception):
    def __init__(self, product_id):
        self.product_id = product_id
        self.message = f"Product with ID {product_id} was not found"
        super().__init__(self.message)



class ProductService():

    def __init__(self,repository: ProductRepository):
        self.product_repository = repository


    def get_product(self,product_id):
        
        product = self.product_repository.find_product(product_id=product_id)

        if product is None:
            raise ProductNotFoundError(product_id)
        return product
        

        

