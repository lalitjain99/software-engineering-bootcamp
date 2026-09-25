import argparse

import grpc

import inventory_pb2
import inventory_pb2_grpc


def reserve_stock(product_id: int, quantity: int) -> None:
    address = "127.0.0.1:50051"

    with grpc.insecure_channel(address) as channel:
        stub = inventory_pb2_grpc.InventoryServiceStub(channel)
        request = inventory_pb2.ReserveStockRequest(
            product_id=product_id,
            quantity=quantity,
        )

        print(
            "Calling remote method:",
            f"ReserveStock(product_id={product_id}, quantity={quantity})",
        )

        try:
            response = stub.ReserveStock(request, timeout=3)
        except grpc.RpcError as error:
            print("RPC failed")
            print("status:", error.code().name)
            print("details:", error.details())
            return

        print("RPC succeeded")
        print("reserved:", response.reserved)
        print("remaining_quantity:", response.remaining_quantity)
        print("message:", response.message)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call the InventoryService ReserveStock RPC"
    )
    parser.add_argument("product_id", type=int)
    parser.add_argument("quantity", type=int)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_arguments()
    reserve_stock(arguments.product_id, arguments.quantity)
