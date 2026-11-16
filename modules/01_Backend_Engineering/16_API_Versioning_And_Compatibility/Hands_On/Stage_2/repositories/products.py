class ProductRepository:
    products = {
        1:{
            "id": 101,
            "name": "Monitor",
            "price": 999.99,
            "category": "Electronics",
            "stock": 3
        },
        2:{
            "id": 102,
            "name": "Keyboard",
            "price": 99.99,
            "category": "Electronics",
            "stock": 6
        },
        3:{
            "id": 103,
            "name": "Mouse",
            "price": 9.99,
            "category": "Electronics",
            "stock": 6
        }
    }

    def get_product(self,product_id: int):
        for product in self.products.values():
            if product["id"] == product_id:
                return product
        return None