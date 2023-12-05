from db.db import initialize_inventory, create_inventory, get_inventory, update_inventory_quantity, delete_inventory
from model.base_model import RequestItem
import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

initialize_inventory()

async def update_inventory(request: RequestItem):
    #if there are enough tokens in inventory, push it along to next service
    #could fail to get tokens
    tokens = get_inventory('tokens')
    if tokens[2] > 0:
        #could fail to update quantity
        new_tokens = tokens[2]-1
        print(new_tokens)
        update_inventory_quantity("tokens", new_tokens)
        #if this is a success then we fine else
        request.data["action"] = "updatedInventory"
        
        #publishing message in UPDATED_INVENTORY queue that delivery service is listening in
        connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
        channel = await connection.channel()
        queue = await channel.declare_queue('updated_inventory_queue')
        message_data = {'request': request.model_dump(), 'event_name': 'UPDATED_INVENTORY'}
        message_body = json.dumps(message_data)
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body.encode()),
            routing_key='updated_inventory_queue',
        )
        #print(f" [x] Sent 'UPDATED_INVENTORY' event with '{message_body}'")
        await connection.close()
    else:
        #publish message with empty inventory event.
        print("Will publish event {:s}".format(request.failures.get("emptyInventory")))
        
async def payment_consumer():
    #listening in queue payment_processed_queue
    #due to using unique queue names for each event, every event in said unique queue
    #is unique to the service
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    queue = await channel.declare_queue('payment_processed_queue')

    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            request = RequestItem(**message_data['request'])
            #print(f"Received PAYMENT_PROCESSED event with request: {request}")
            await update_inventory(request)

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
    asyncio.run(payment_consumer())