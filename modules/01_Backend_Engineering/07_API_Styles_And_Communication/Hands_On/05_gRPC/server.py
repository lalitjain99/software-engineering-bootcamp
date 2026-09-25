from concurrent import futures

import grpc

import inventory_pb2
import inventory_pb2_grpc


stock_by_product_id: dict[int, int] = {
    101: 10,
    102: 5,
}


class InventoryService(inventory_pb2_grpc.InventoryServiceServicer):
    def ReserveStock(
        self,
        request: inventory_pb2.ReserveStockRequest,
        context: grpc.ServicerContext,
    ) -> inventory_pb2.ReserveStockResponse:
        print(
            "ReserveStock received:",
            f"product_id={request.product_id}",
            f"quantity={request.quantity}",
        )

        if request.quantity <= 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "quantity must be greater than zero",
            )

        if request.product_id not in stock_by_product_id:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"product {request.product_id} was not found",
            )

        available_quantity = stock_by_product_id[request.product_id]

        if request.quantity > available_quantity:
            return inventory_pb2.ReserveStockResponse(
                reserved=False,
                remaining_quantity=available_quantity,
                message="Insufficient stock",
            )

        remaining_quantity = available_quantity - request.quantity
        stock_by_product_id[request.product_id] = remaining_quantity

        return inventory_pb2.ReserveStockResponse(
            reserved=True,
            remaining_quantity=remaining_quantity,
            message="Stock reserved",
        )


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryService(),
        server,
    )

    address = "127.0.0.1:50051"
    server.add_insecure_port(address)
    server.start()

    print(f"Inventory gRPC server listening on {address}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Stopping Inventory gRPC server")
        server.stop(grace=2).wait()


if __name__ == "__main__":
    serve()
