from db.db import get_user, update_user_credits, initialize_payments, create_payment, get_payment, delete_payment
from services.inventory import update_inventory
from model.base_model import RequestItem

initialize_payments()

def process_payment(request: RequestItem):
    #if user has enough credits, push it along to next service
    #potential problems could be when -> user doesnt have enough credits,next service is occupied with smth else.
    request.data["action"] = "processPayment"
    if request.data.get("credits") > 10:
        credits = request.data.get("credits")
        #could fail to update user credits
        update_user_credits(request.data.get("userId"), credits-10)
        #could fail to start creating payment
        payment_id = create_payment(request.data.get("userId"), request.data.get("orderId"))
        request.data["paymentId"] = payment_id
        #could fail to start updating inventory
        update_inventory(request)
    else:
        #publish message with insufficient funds event.
        print("Will publish event {:s}".format(request.failures.get("insufficientFunds")))
        print('User {:d} has insufficient credits.'.format(request.data.get("userId")))