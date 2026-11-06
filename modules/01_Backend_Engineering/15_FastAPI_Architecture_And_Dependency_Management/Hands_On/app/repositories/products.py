class ProductRepository:
    products = {"1":
        {
            "id" : 101,
            "name": "Monitor",
            "price": 5000,
            "stock": 5,
            "category": "electronics"
        },
        "2":
        {
            "id" : 102,
            "name": "Keyboard",
            "price": 2000,
            "stock": 15,
            "category": "electronics"
        },
        "3":
        {
            "id" : 103,
            "name": "Mouse",
            "price": 1000,
            "stock": 20,
            "category": "electronics"       
        }
    }

    def find_product(id:int,products):
        for ele,product in products:
            if id in product:
                return product
        return None