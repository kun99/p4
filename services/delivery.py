from db.db import initialize_delivery, create_delivery, get_delivery, delete_delivery

initialize_delivery()

def deliver_order(user_id, order_id, payment_id, inventory):
    #deliver order unless there is some problem?
    create_delivery(user_id, order_id, payment_id, inventory)
    print("Success")
    return True