from db.db import create_delivery, get_delivery, delete_delivery
from model.base_model import RequestItem
import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

#create delivery record and report success
#publishes event DELIVERED_ORDER if it works as expected
#publishes event FAILED_DELIVERY if something fails for some reason
async def deliver_order(request: RequestItem):
    try:
        create_delivery(request.data.get("userId"), request.data.get("orderId"), request.data.get("paymentId"))
        request.data["action"] = "deliveredOrder"
        await publish_message(request, 'DELIVERED_ORDER')
    except Exception as e:
        await publish_message(request, 'FAILED_DELIVERY')

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
async def start_delivery():
    connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
    channel = await connection.channel()
    queue = await channel.declare_queue('')
    
    await queue.bind(exchange="direct_event", routing_key="START_DELIVERY")
    
    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            request = RequestItem(**message_data['request'])
            await deliver_order(request)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    await asyncio.Event().wait()
    
if __name__ == "__main__":
    asyncio.run(start_delivery())