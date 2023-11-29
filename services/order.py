from fastapi import FastAPI
from db.db import initialize_users, create_user, get_user, initialize_orders, create_order, get_order, delete_order
from services.payment import process_payment
from model.base_model import RequestItem

app = FastAPI()

initialize_users()
initialize_orders()

@app.post("/create_order")
async def order_creation(request: RequestItem):
    #request comes with user data i guess? containing info on their username, id
    #if user exists in database use user data else create user
    #could fail to get user
    user = get_user(request.data.get("name"))
    id = 0
    credits = 100
    if user is None:
        #could fail to create user
        created_id = create_user(request.data.get("name"))
        id = created_id
    else:
        id = user[0]
        credits = user[2]
    #could fail to create order
    order_id = create_order(id, request.data.get("name"))
    request.data["userId"] = id
    request.data["orderId"] = order_id
    request.data["credits"] = credits
    print("Has tokens {:d}".format(credits))
    #could fail to start processing payment
    process_payment(request)
        
# {
#   "action": "placeOrder",
#   "data": {
#     "name": "user",
#   },
#   "failures": {
#      "orderFailure": "cancelOrder",
#      "paymentFailure": "cancelPayment",
#      "emptyInventory": "reverseInventory",
#      "deliveryFailure": "cancelDelivery",
#      "databaseFailure": "cancelProcess",
#      "insufficientFunds": "cancelPayment",
#      "inventoryFailure": "reverseInventory",
#   }    
# }
