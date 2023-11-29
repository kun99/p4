from db.db import get_user, initialize_inventory, create_inventory, get_inventory, update_inventory_quantity, delete_inventory
from services.delivery import deliver_order

initialize_inventory()

def update_inventory(user_id, order_id, payment_id):
    #if there are enough tokens in inventory, push it along to next service
    #could fail to get tokens
    tokens = get_inventory('tokens')
    if tokens[2] > 0:
        #could fail to update quantity
        new_tokens = tokens[2]-1
        print(new_tokens)
        update_inventory_quantity("tokens", new_tokens)
        #if this is a success then we fine else
        if not deliver_order(user_id, order_id, payment_id, "tokens"):
            print("rollback")
    else:
        #publish message with empty inventory event.
        print("rollback")