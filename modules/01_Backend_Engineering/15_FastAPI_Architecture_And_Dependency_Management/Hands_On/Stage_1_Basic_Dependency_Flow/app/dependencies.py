from app.repositories.products import ProductRepository
from app.services.products import ProductService

def get_product_service():
    repository = ProductRepository()
    service = ProductService(repository)
    return service