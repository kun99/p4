from db.db import update_user_credits, initialize_payments, create_payment, get_payment, delete_payment
from model.base_model import RequestItem
import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

initialize_payments()

async def process_payment(request: RequestItem):
    #if user has enough credits, push it along to next service
    #potential problems could be when -> user doesnt have enough credits,next service is occupied with smth else.
    print(request.data.get("credits"))
    if request.data.get("credits") > 10:
        print('User {:d} has sufficient credits.'.format(request.data.get("userId")))
        credits = request.data.get("credits")
        #could fail to update user credits
        update_user_credits(request.data.get("userId"), credits-10)
        #could fail to start creating payment
        payment_id = create_payment(request.data.get("userId"), request.data.get("orderId"))
        request.data["paymentId"] = payment_id
        #could fail to start updating inventory
        request.data["action"] = "processedPayment"
        
        #publishing message in PAYMENT_PROCESSED queue that inventory service is listening in
        connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
        channel = await connection.channel()
        queue = await channel.declare_queue('payment_processed_queue')
        message_data = {'request': request.model_dump(), 'event_name': 'PAYMENT_PROCESSED'}
        message_body = json.dumps(message_data)
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body.encode()),
            routing_key='payment_processed_queue',
        )
        #print(f" [x] Sent 'PAYMENT_PROCESSED' event with '{message_body}'")
        await connection.close()
    else:
        #publish message with insufficient funds event.
        print("Will publish event {:s}".format(request.failures.get("insufficientFunds")))
        print('User {:d} has insufficient credits.'.format(request.data.get("userId")))
    
async def order_consumer():
    #listening in queue order_created_queue
    #due to using unique queue names for each event, every event in said unique queue
    #is unique to the service
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    queue = await channel.declare_queue('order_created_queue')

    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            request = RequestItem(**message_data['request'])
            #print(f"Received ORDER_CREATED event with request: {request}")
            await process_payment(request)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass

    await connection.close()
    
if __name__ == "__main__":
    asyncio.run(order_consumer())