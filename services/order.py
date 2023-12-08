from db.db import create_user, get_user, delete_user, create_order, get_order, delete_order
from model.base_model import RequestItem
import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")
    
#if user exists in database use user data else create user
#create an order and update request data
#publishes event ORDER_CREATED when succesful
#publishes event ORDER_FAILED when unsuccesful
async def order_creation(request: RequestItem):
    step = 0
    try:
        user = await get_user(request.data.get("name"))
        id = 0
        credits = 100
        if user is None:
            created_id = await create_user(request.data.get("name"))
            id = created_id
            request.data["created"] = True
        else:
            id = user[0]
            credits = user[2]
            request.data["created"] = False
        request.data["userId"] = id
        request.data["credits"] = credits
        step = 1
        order_id = await create_order(id, request.data.get("name"))
        request.data["orderId"] = order_id
        step = 2
        if request.action == "orderFail":
            raise Exception()
        await publish_message(request, "ORDER_CREATED")
        
    except Exception as e:
        await rollback_order(request, step)

#undo all changes that were made in order
#publish event to sec that means that the transaction failed and all rollbacks were carried out
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), after=lambda retry_state: print("Timeout"))
async def rollback_order(request: RequestItem, step):
    created = request.data["created"]
    try:
        print("Rolling back order")
        if step > 0 and created:
            id = request.data["userId"]
            print(f"Deleting user with id {id}")
            await delete_user(request.data["userId"])
        if step > 1:
            id = request.data["orderId"]
            print(f"Deleting order with id {id}")
            await delete_order(request.data["orderId"])
        await publish_message(request, "ORDER_FAILED")
            
    except Exception as e:
        print(e)
        print("Couldn't rollback order")
    
#publishes an event for SEC            
async def publish_message(request: RequestItem, event):
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange("direct_event", aio_pika.ExchangeType.DIRECT)

    message_data = {'request': request.model_dump(), 'event_name': event}
    message_body = json.dumps(message_data)
    await exchange.publish(
        aio_pika.Message(body=message_body.encode()),
        routing_key=event,
    )
    await connection.close()
 
#listens for events from SEC       
async def start_consumer():
    print("FUCK")
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    queue = await channel.declare_queue('')
    exchange = await channel.declare_exchange("direct_event", type=aio_pika.ExchangeType.DIRECT)
    await queue.bind(exchange=exchange, routing_key="TRANSACTION_STARTED")
    await queue.bind(exchange=exchange, routing_key="ROLLBACK_ORDER")
    
    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            event_type = message.routing_key
            request = RequestItem(**message_data['request'])
            if event_type == "TRANSACTION_STARTED":
                await order_creation(request)
            elif event_type == "ROLLBACK_ORDER":
                await rollback_order(request, 2)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    await asyncio.Event().wait()
    
if __name__ == "__main__":
    asyncio.run(start_consumer())