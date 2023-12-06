from db.db import create_user, get_user, create_order, get_order, delete_order
from model.base_model import RequestItem
from dotenv import load_dotenv
import os
import json
import aio_pika
import asyncio

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

async def order_creation(request: RequestItem):
    #request comes with user data i guess? containing info on their username, id
    #if user exists in database use user data else create user
    user = get_user(request.data.get("name"))
    if user is not None:
        id = 0
        credits = 100
        if user == "NoUser":
            created_id = create_user(request.data.get("name"))
            if created_id is not None:
                id = created_id
            else:
                print("GONNA SEND OUT A FAILED TO ACCESS DB EVENT")
        else:
            id = user[0]
            credits = user[2]
        order_id = create_order(id, request.data.get("name"))
        if order_id is not None:
            request.data["userId"] = id
            request.data["orderId"] = order_id
            request.data["credits"] = credits
        else:
            print("GONNA SEND OUT A FAILED TO ACCESS DB EVENT")
        #publishing message in ORDER_CREATED queue that payment service is listening in
        try:
            connection = await aio_pika.connect_robust(
                host=host,
                port=port,
            )
            channel = await connection.channel()
            queue = await channel.declare_queue('order_created_queue')
            message_data = {'request': request.model_dump(), 'event_name': 'ORDER_CREATED'}
            message_body = json.dumps(message_data)
            await channel.default_exchange.publish(
                aio_pika.Message(body=message_body.encode()),
                routing_key='order_created_queue',
            )
            #print(f" [x] Sent 'ORDER_CREATED' event with '{message_body}'")
        except Exception as e:
            print("Failed to publish event")
        finally:
            await connection.close()
    else:
        print("GONNA SEND OUT A FAILED TO ACCESS DB EVENT")
    
async def start_consumer():
    #listening in queue transaction_started_queue
    #due to using unique queue names for each event, every event in said unique queue
    #is unique to the service
    try: 
        connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
        channel = await connection.channel()
        queue = await channel.declare_queue('transaction_started_queue')

        async def callback(message):
            try:
                request_data_str = message.body.decode()
                message_data = json.loads(request_data_str)
                request = RequestItem(**message_data['request'])
                #print(f"Received TRANSACTION_STARTED event with request: {request}")
                await order_creation(request)

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

if __name__ == "__main__":
    asyncio.run(start_consumer())