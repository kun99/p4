from db.db import update_user_credits, create_payment, get_payment, delete_payment
from model.base_model import RequestItem
import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

#user pays for order and update request data
#publishes event PAYMENT_PROCESSED when succesful
#publishes event INSUFFICIENT_FUNDS when user doesnt have sufficient funds
#publishes event PAYMENT_FAILED when unsuccesful
async def process_payment(request: RequestItem):
    try:
        if request.data.get("credits") > 10:
            credits = request.data.get("credits")
            update_user_credits(request.data.get("userId"), credits-10)
            payment_id = create_payment(request.data.get("userId"), request.data.get("orderId"))
            if payment_id is not None:
                request.data["paymentId"] = payment_id
                request.data["action"] = "processedPayment"
                await publish_message(request, 'PAYMENT_PROCESSED')
        else:
            await publish_message(request, 'INSUFFICIENT_FUNDS')
    
    except Exception as e:
        request.data["action"] = "paymentFailed"
        await publish_message(request, 'PAYMENT_FAILED')
        
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
async def start_payment():
    connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
    channel = await connection.channel()
    queue = await channel.declare_queue('')
    
    await queue.bind(exchange="direct_event", routing_key="START_PAYMENT")
    
    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            request = RequestItem(**message_data['request'])
            await process_payment(request)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    await asyncio.Event().wait()
    
if __name__ == "__main__":
    asyncio.run(start_payment())