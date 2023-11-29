from db import get_user, update_user_credits, initialize_payments, create_payment, get_payment, delete_payment
from inventory import update_inventory

initialize_payments()

def process_payment(user_id, order_id):
    #if user has enough credits, push it along to next service
    #potential problems could be when -> user doesnt have enough credits,next service is occupied with smth else.
    #could fail to get user
    user = get_user(user_id)
    if user.credits > 10:
        credits = user.credits
        #could fail to update user credits
        update_user_credits(user_id, credits-10)
        #could fail to start creating payment
        payment_id = create_payment(user_id, order_id)
        #could fail to start updating inventory
        update_inventory(user_id, order_id, payment_id)
    else:
        #publish message with insufficient funds event.
        print("rollback")