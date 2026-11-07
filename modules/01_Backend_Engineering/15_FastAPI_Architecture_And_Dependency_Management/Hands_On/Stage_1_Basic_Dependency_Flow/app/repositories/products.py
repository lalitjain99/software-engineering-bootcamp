class ProductRepository:
    products = {1:
        {
            "id" : 101,
            "name": "Monitor",
            "price": 5000,
            "stock": 5,
            "category": "electronics"
        },
        2:
        {
            "id" : 102,
            "name": "Keyboard",
            "price": 2000,
            "stock": 15,
            "category": "electronics"
        },
        3:
        {
            "id" : 103,
            "name": "Mouse",
            "price": 1000,
            "stock": 20,
            "category": "electronics"       
        }
    }

    def find_product(self,product_id:int):
        for product in self.products.values():
            if product["id"] == product_id:
                return product
        return None