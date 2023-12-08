from db.db import create_delivery, get_delivery, delete_delivery
from model.base_model import RequestItem
import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()
host = os.getenv("HOST")
port = int(os.getenv("PORT"))

#create delivery record and report success
#publishes event DELIVERED_ORDER if it works as expected
#publishes event FAILED_DELIVERY if something fails for some reason
async def deliver_order(request: RequestItem):
    step = 0
    try:
        id = await create_delivery(request.data.get("userId"), request.data.get("orderId"), request.data.get("paymentId"))
        request.data["deliveryId"] = id
        step = 1
        if request.action == "deliveryFail":
            raise Exception()
        await publish_message(request, 'DELIVERED_ORDER')
    except Exception as e:
        await rollback_delivery(request, step)

#undo all changes that were made in delivery
#publish event to sec that will trigger rollback for inventory   
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), after=lambda retry_state: print("Timeout"))
async def rollback_delivery(request: RequestItem, step):
    try:
        print("Rolling back delivery")
        if step > 0:
            await delete_delivery(request.data["deliveryId"])
        await publish_message(request, 'FAILED_DELIVERY')
            
    except Exception as e:
        print(e)
        print("Couldn't rollback delivery")

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