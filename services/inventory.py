from db.db import create_inventory, get_inventory, update_inventory_quantity, delete_inventory
from model.base_model import RequestItem
import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

load_dotenv()
host = os.getenv("HOST")
port = os.getenv("PORT")

#inventory is updated by -=1
#publishes event UPDATED_INVENTORY when succesful
#publishes event OUT_OF_STOCK when out of stock
#publishes event INVENTORY_FAILED when unsuccesful
async def update_inventory(request: RequestItem):
    try:
        tokens = get_inventory('tokens')
        if tokens[2] > 0:
            new_tokens = tokens[2]-1
            update_inventory_quantity("tokens", new_tokens)
            request.data["action"] = "updatedInventory"
            await publish_message(request, 'UPDATED_INVENTORY')
        else:
            await publish_message(request, 'OUT_OF_STOCK')
    except Exception as e:
        await publish_message(request, 'INVENTORY_FAILED')
        
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
async def start_inventory():
    connection = await aio_pika.connect_robust(
            host=host,
            port=port,
        )
    channel = await connection.channel()
    queue = await channel.declare_queue('')
    
    await queue.bind(exchange="direct_event", routing_key="START_INVENTORY")
    
    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            request = RequestItem(**message_data['request'])
            await update_inventory(request)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    await asyncio.Event().wait()
    
if __name__ == "__main__":
    asyncio.run(start_inventory())