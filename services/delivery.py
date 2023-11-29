from db.db import initialize_delivery, create_delivery, get_delivery, delete_delivery
from model.base_model import RequestItem

initialize_delivery()

def deliver_order(request: RequestItem, inventory):
    #deliver order unless there is some problem?
    request.data["action"] = "deliverOrder"
    create_delivery(request.data.get("userId"), request.data.get("orderId"), request.data.get("paymentId"), inventory)
    print("Success")
    return True