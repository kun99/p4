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
    step = 0
    try:
        print(request.data)
        if request.data.get("credits") > 10:
            credits = request.data.get("credits")
            user_id = request.data.get("userId")
            user = await update_user_credits(request.data.get("name"), user_id, credits-10)
            request.data["credits"] = user[2]
            print(request.data.get("credits"))
            step = 1
            payment_id = await create_payment(request.data.get("userId"), request.data.get("orderId"))
            if payment_id is not None:
                request.data["paymentId"] = payment_id
                request.data["action"] = "processedPayment"
                step = 2
                await publish_message(request, 'PAYMENT_PROCESSED')
        else:
            request.data["action"] = "insufficientFunds"
            await rollback_payment(request, step)
    
    except Exception as e:
        request.data["action"] = "paymentFailed"
        await rollback_payment(request, step)
        
async def rollback_payment(request: RequestItem, step):
    credits = request.data.get("credits")
    try:
        print("Rolling back payment")
        if step == 0:
            await publish_message(request, 'INSUFFICIENT_FUNDS')
        else:
            if step > 0:
                print("Refunding credits")
                await update_user_credits(request.data.get("name"), request.data["userId"], credits+10)
            if step > 1:
                print("Deleting payment")
                await delete_payment(request.data["paymentId"])
            await publish_message(request, 'PAYMENT_FAILED')
        
    except Exception as e:
        print(e)
        print("Couldn't rollback payment")
        
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
    exchange = await channel.declare_exchange("direct_event", type=aio_pika.ExchangeType.DIRECT)
    await queue.bind(exchange=exchange, routing_key="START_PAYMENT")
    await queue.bind(exchange=exchange, routing_key="ROLLBACK_PAYMENT")
    
    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            event_type = message.routing_key
            request = RequestItem(**message_data['request'])
            if event_type == "START_PAYMENT":
                await process_payment(request)
            elif event_type == "ROLLBACK_PAYMENT":
                await rollback_payment(request, 2)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    await asyncio.Event().wait()
        
if __name__ == "__main__":
    asyncio.run(start_payment())