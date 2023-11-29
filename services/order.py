from fastapi import FastAPI
from db.db import initialize_users, create_user, get_user, initialize_orders, create_order, get_order, delete_order
from services.payment import process_payment

app = FastAPI()

initialize_users()
initialize_orders()

@app.post("/create_order")
async def order_creation(user_id, name):
    #request comes with user data i guess? containing info on their username, id
    #if user exists in database use user data else create user
    #could fail to get user
    user = get_user(user_id)
    if user is None:
        #could fail to create user
        created_id = create_user(name)
        #could fail to create order
        order_id = create_order(created_id, name)
        #could fail to start processing payment
        process_payment(created_id, order_id)
    else:
        #could fail to create order
        order_id = create_order(user[0], user[1])
        #could fail to start processing payment
        process_payment(user[0], order_id)