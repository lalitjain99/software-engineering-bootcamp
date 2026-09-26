products: dict[int, dict] = {
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
    def __init__(self,products):
        self.products: list[dict] = products
        self.next_id = 103

    def get_product(self,product_id:int):
        if product_id not in product_id:
            return
        return self.products[product_id]

    def find_product_by_sku(self,sku:str):
        for product_id,details in self.products:
            if details["sku"] == sku:
                return self.products[product_id]
            
    def list_product(self):
        return self.products

    def add_product(
        self,
        name: str,
        sku: str,
        price: float,
    ) -> dict:
        product = {
            "id": self.next_id,
            "name": name,
            "sku": sku,
            "price": price,
        }

        self.next_id += 1
        self.products.append(product)
        return product