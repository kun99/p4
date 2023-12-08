from db.db import create_inventory, get_inventory, update_inventory_quantity, delete_inventory
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

#inventory is updated by -=1
#publishes event UPDATED_INVENTORY when succesful
#publishes event OUT_OF_STOCK when out of stock
#publishes event INVENTORY_FAILED when unsuccesful
async def update_inventory(request: RequestItem):
    step = 0
    try:
        if request.action == "outOfStock":
            step = -1
            raise Exception()
        tokens = await get_inventory('tokens')
        if tokens[2] > 0:
            new_tokens = tokens[2]-1
            await update_inventory_quantity(tokens[0], new_tokens)
            step = 1
            if request.action == "inventoryFail":
                raise Exception()
            await publish_message(request, 'UPDATED_INVENTORY')
        else:
            await rollback_inventory(request, step-1)
    except Exception as e:
        await rollback_inventory(request, step)
        
#undo all changes that were made in inventory
#publish event to sec that will trigger rollback for payment
@retry(stop=stop_after_attempt(5), wait=wait_fixed(1), after=lambda retry_state: print("Timeout"))   
async def rollback_inventory(request: RequestItem, step):
    try:
        print("Rolling back inventory")
        if step == -1:
            print("HERE")
            await publish_message(request, 'OUT_OF_STOCK')
        elif step > 0:
            tokens = await get_inventory('tokens')
            await update_inventory_quantity(request.data["userId"], tokens[2]+1)
            await publish_message(request, 'INVENTORY_FAILED')
            
    except Exception as e:
        print(e)
        print("Couldn't rollback inventory")
        
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
    exchange = await channel.declare_exchange("direct_event", type=aio_pika.ExchangeType.DIRECT)
    await queue.bind(exchange=exchange, routing_key="START_INVENTORY")
    await queue.bind(exchange=exchange, routing_key="ROLLBACK_INVENTORY")
    
    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            event_type = message.routing_key
            request = RequestItem(**message_data['request'])
            if event_type == "START_INVENTORY":
                await update_inventory(request)
            elif event_type == "ROLLBACK_INVENTORY":
                await rollback_inventory(request, 1)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

        await message.ack()

    await queue.consume(callback)
    await asyncio.Event().wait()
        
if __name__ == "__main__":
    asyncio.run(start_inventory())