from db import create_user, get_user, initialize_orders, create_order, get_order, delete_order
from payment import process_payment
from main import app

initialize_orders()

@app.post("/create_order/{name}")
async def order_creation(user_id, name):
    #request comes with user data i guess? containing info on their username, id
    #if user exists in database use user data else create user
    #could fail to get user
    user = get_user(user_id)
    if user is None:
        #could fail to create user
        created_id = create_user({"name": name, "credits": 100})
        #could fail to create order
        order_id = create_order(created_id)
        #could fail to start processing payment
        process_payment(created_id, order_id)
    else:
        #could fail to create order
        order_id = create_order(user.id)
        #could fail to start processing payment
        process_payment(user.id, order_id)