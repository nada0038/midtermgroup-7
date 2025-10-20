import os, json
import azure.functions as func
from azure.cosmos import CosmosClient

# Uses your app setting: CosmosDBConnection
CONN = os.environ["CosmosDBConnection"]
client = CosmosClient.from_connection_string(CONN)
db = client.get_database_client("storedb")
container = db.get_container_client("items")

def main(req: func.HttpRequest) -> func.HttpResponse:
    method = req.method.upper()
    item_id = req.route_params.get("id")  # present for PUT/DELETE
    category = req.params.get("category")  # partition key for DELETE/PUT

    if method == "GET":
        items = list(container.read_all_items())
        return func.HttpResponse(json.dumps(items), mimetype="application/json")

    if method == "POST":
        try:
            body = req.get_json()
        except Exception:
            return func.HttpResponse("Invalid JSON", status_code=400)
        if "category" not in body:
            return func.HttpResponse("category required", status_code=400)
        # let Cosmos generate an id or use client side one if present
        created = container.create_item(body)
        return func.HttpResponse(json.dumps({"id": created["id"]}), mimetype="application/json", status_code=201)

    if method == "PUT":
        if not item_id or not category:
            return func.HttpResponse("id and category required", status_code=400)
        try:
            body = req.get_json()
        except Exception:
            return func.HttpResponse("Invalid JSON", status_code=400)
        body["id"] = item_id
        body["category"] = category
        container.upsert_item(body)
        return func.HttpResponse(status_code=200)

    if method == "DELETE":
        if not item_id or not category:
            return func.HttpResponse("id and category required", status_code=400)
        container.delete_item(item=item_id, partition_key=category)
        return func.HttpResponse(status_code=204)

    return func.HttpResponse("Method not allowed", status_code=405)

