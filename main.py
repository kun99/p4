from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import aio_pika
import asyncio
import os
import json
from model.base_model import RequestItem
from initialization import initialize_tables

app = FastAPI()

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

@app.post("/buy_token")
async def buy_token(request: RequestItem):   
    try:
        if request.action == "failAtStart":
            raise Exception("Fail at start")     
        #publishing message in TRANSACTION_STARTED queue that order service is listening in
        connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
        channel = await connection.channel()
        exchange = await channel.declare_exchange('TRANSACTION_STARTED', aio_pika.ExchangeType.FANOUT)
        message_data = {'request': request.dict(), 'event_name': 'TRANSACTION_STARTED'}
        message_body = json.dumps(message_data)
        await exchange.publish(
            aio_pika.Message(body=message_body.encode()),
            routing_key='',
        )
        #print(f" [x] SENT TRANSACTION_STARTED event with {message_body}")
        await connection.close()
    except Exception as e:
        return JSONResponse(content={"error": 'Transaction failed to start'}, status_code=500)
    
async def process_event(message_data):
    event_type = message_data.get('event_type')

    if event_type == 'EVENT_TYPE_A':
        # Trigger microservice A
        print("Running microservice A with data:", message_data)

    elif event_type == 'EVENT_TYPE_B':
        # Trigger microservice B
        print("Running microservice B with data:", message_data)
    
async def event_listener():
    try: 
        connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
        channel = await connection.channel()
        queue = await channel.declare_queue('')
        
        await queue.bind(exchange="direct_exchange", routing_key="EVENT_TYPE_A")
        await queue.bind(exchange="direct_exchange", routing_key="EVENT_TYPE_B")

        async def callback(message):
            try:
                request_data_str = message.body.decode()
                message_data = json.loads(request_data_str)
                request = RequestItem(**message_data['request'])
                #print(f"Received TRANSACTION_STARTED event with request: {request}")
                await process_event(message_data)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

            await message.ack()

        await queue.consume(callback)
        await asyncio.Event().wait()
        
    except Exception as e:
        print("Couldn't be set up to receive any messages")
    finally:
        if connection is not None and not connection.is_closed:
            await connection.close()
    
async def handle_event(event):
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()

    if event['name'] == 'Microservice1Completed':
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({'name': 'Microservice2Started', 'data': event['data']}).encode()),
            routing_key='saga_events'
        )   
    elif event['name'] == 'Microservice2Failed':
        await compensate_microservice1(event['data'])

    await connection.close()

# async def compensate_microservice1(data):
#     connection = await aio_pika.connect_robust(
#         host=host,
#         port=port,
#     )
#     channel = await connection.channel()

#     await channel.default_exchange.publish(
#         aio_pika.Message(body=json.dumps({'name': 'CompensateMicroservice1', 'data': data}).encode()),
#         routing_key='saga_events'
#     )

#     await connection.close()
    
async def tables():
    if not initialize_tables():
        return JSONResponse(content={"error": 'Not your fault. The db just isnt set up as expected.'}, status_code=500)

#if tables aren't already initialized
#if they are just uncomment.
if __name__ == "__main__":
    tables()
    asyncio.run(event_listener())

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