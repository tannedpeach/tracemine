"""In-memory order service before idempotency support."""

from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)
    orders = []

    @app.post("/orders")
    def create_order():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="expected object"), 400
        sku, quantity = data.get("sku"), data.get("quantity", 1)
        if not isinstance(sku, str) or not sku.strip():
            return jsonify(error="invalid sku"), 400
        if type(quantity) is not int or quantity < 1:
            return jsonify(error="invalid quantity"), 400
        order = {"id": len(orders) + 1, "sku": sku.strip(), "quantity": quantity}
        orders.append(order)
        return jsonify(order), 201

    @app.get("/orders")
    def list_orders():
        return jsonify(orders=orders)

    return app
