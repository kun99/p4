from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import aio_pika
import asyncio
import os
import json
from model.base_model import RequestItem

app = FastAPI()

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

transaction_completed = asyncio.Event()

@app.post("/buy_token")
async def buy_token(request: RequestItem):
    try:
        asyncio.create_task(event_listener())
        await start_transaction(request)
    except Exception as e:
        return "UNKNOWN"

async def start_transaction(request: RequestItem):   
    if request.action == "failAtStart":
        raise Exception("Fail at start")     
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange("direct_event", aio_pika.ExchangeType.DIRECT)
    
    message_data = {'request': request.dict(), 'event_name': 'TRANSACTION_STARTED'}
    message_body = json.dumps(message_data)
    await exchange.publish(
        aio_pika.Message(body=message_body.encode()),
        routing_key='TRANSACTION_STARTED',
    )
    await connection.close()
    
async def process_event(event_type):
    #compensating transactions coming soon ~ in 5 hrs or so :)
    print(f"RECEIVED EVENT {event_type}")
    publishing_event = ''
    if event_type == 'ORDER_CREATED':
        publishing_event = 'START_PAYMENT'   
    elif event_type == 'ORDER_FAILED':
        print('order failed')    
    elif event_type == 'PAYMENT_PROCESSED':
        publishing_event = 'START_INVENTORY'   
    elif event_type == 'PAYMENT_FAILED':
        print('payment failed')   
    elif event_type == 'UPDATED_INVENTORY':
        publishing_event = 'START_DELIVERY'    
    elif event_type == 'INVENTORY_FAILED':
        print('inventory failed')     
    elif event_type == 'DELIVERED_ORDER':
        print("SUCCESS")
        transaction_completed.set()
    elif event_type == 'FAILED_DELIVERY':
        print('delivery failed')    
    elif event_type == 'INSUFFICIENT_FUNDS':
        print('insufficient funds')
    elif event_type == 'OUT_OF_STOCK':
        print('we out')
    return publishing_event
    
async def publish_event(publishing_event, request: RequestItem):
    #retries, circuit break later
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange("direct_event", aio_pika.ExchangeType.DIRECT)
    message_data = {'request': request.model_dump(), 'event_name': publishing_event}
    message_body = json.dumps(message_data)
    await exchange.publish(
        aio_pika.Message(body=message_body.encode()),
        routing_key=publishing_event,
    )
    await connection.close()
    
async def event_listener():
    while True:
        try: 
            done = False
            connection = await aio_pika.connect_robust(
                host=host,
                port=port,
            )
            channel = await connection.channel()
            queue = await channel.declare_queue('')
            exchange = await channel.declare_exchange("direct_event", type=aio_pika.ExchangeType.DIRECT)
            #await queue.bind(exchange=exchange, routing_key="TRANSACTION_STARTED")
            await queue.bind(exchange=exchange, routing_key="ORDER_CREATED")
            await queue.bind(exchange=exchange, routing_key="ORDER_FAILED") #TIMEOUT
            #await queue.bind(exchange=exchange, routing_key="START_PAYMENT")
            await queue.bind(exchange=exchange, routing_key="PAYMENT_PROCESSED")
            await queue.bind(exchange=exchange, routing_key="PAYMENT_FAILED") #TIMEOUT
            #await queue.bind(exchange=exchange, routing_key="START_INVENTORY")
            await queue.bind(exchange=exchange, routing_key="UPDATED_INVENTORY")
            await queue.bind(exchange=exchange, routing_key="INVENTORY_FAILED") #TIMEOUT
            #await queue.bind(exchange=exchange, routing_key="START_DELIVERY")
            await queue.bind(exchange=exchange, routing_key="DELIVERED_ORDER") #SUCCESS
            await queue.bind(exchange=exchange, routing_key="FAILED_DELIVERY") #UNKNOWN
            await queue.bind(exchange=exchange, routing_key="INSUFFICIENT_FUNDS") #INSUFFICIENT_FUND
            await queue.bind(exchange=exchange, routing_key="OUT_OF_STOCK") #OUT OF STOCK
        
            async def callback(message):
                try:
                    request_data_str = message.body.decode()
                    message_data = json.loads(request_data_str)
                    event_type = message.routing_key
                    if event_type=='DELIVERED_ORDER':
                        done = True
                    request = RequestItem(**message_data['request'])
                    event = await process_event(event_type)
                    await publish_event(event, request)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                await message.ack()

            await queue.consume(callback)
            
            if done:
                break
            await asyncio.sleep(1)
            
        except Exception as e:
            print("Couldn't be set up to receive any messages")
        finally:
            if connection is not None and not connection.is_closed:
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