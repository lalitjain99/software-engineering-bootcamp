from app.repositories.products import ProductRepository
from app.services.products import ProductService

def composition():
    repository = ProductRepository
    service = ProductService(repository)
    return service