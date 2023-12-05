from fastapi import FastAPI
from dotenv import load_dotenv
import aio_pika
import os
import json
from model.base_model import RequestItem

app = FastAPI()

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

@app.post("/buy_token")
async def buy_token(request: RequestItem):
    #publishing message in TRANSACTION_STARTED queue that order service is listening in
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    queue = await channel.declare_queue('transaction_started_queue')
    message_data = {'request': request.dict(), 'event_name': 'TRANSACTION_STARTED'}
    message_body = json.dumps(message_data)
    await channel.default_exchange.publish(
        aio_pika.Message(body=message_body.encode()),
        routing_key='transaction_started_queue',
    )
    #print(f" [x] SENT TRANSACTION_STARTED event with {message_body}")
    
    await connection.close()

# request looks like this
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