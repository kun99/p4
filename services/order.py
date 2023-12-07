from db.db import initialize_users, initialize_orders, create_user, get_user, create_order, get_order, delete_order
from model.base_model import RequestItem
from dotenv import load_dotenv
import os
import json
import aio_pika
import asyncio

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")
    
#if user exists in database use user data else create user
#create an order and update request data
#publishes event ORDER_CREATED when succesful
#publishes event ORDER_FAILED when unsuccesful
async def order_creation(request: RequestItem):
    try:
        user = get_user(request.data.get("name"))
        id = 0
        credits = 100
        if user is None:
            created_id = create_user(request.data.get("name"))
            id = created_id
        else:
            id = user[0]
            credits = user[2]
        order_id = create_order(id, request.data.get("name"))
        request.data["action"] = "orderCreated"
        request.data["userId"] = id
        request.data["orderId"] = order_id
        request.data["credits"] = credits
        await publish_message(request, "ORDER_CREATED")
        
    except Exception as e:
        request.data["action"] = "orderFailed"
        await publish_message(request, "ORDER_FAILED")

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
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    queue = await channel.declare_queue('')
    exchange = await channel.declare_exchange("direct_event", type=aio_pika.ExchangeType.DIRECT)
    await queue.bind(exchange=exchange, routing_key="TRANSACTION_STARTED")
    
    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            request = RequestItem(**message_data['request'])
            await order_creation(request)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(start_consumer())