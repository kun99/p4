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

async def deliver_order(request: RequestItem):
    #deliver order unless there is some problem?
    create_delivery(request.data.get("userId"), request.data.get("orderId"), request.data.get("paymentId"))
    request.data["action"] = "deliveredOrder"
    print("Succesful delivery!")
    return request

async def inventory_consumer():
    #listening in queue updated_inventory_queue
    #due to using unique queue names for each event, every event in said unique queue
    #is unique to the service
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    queue = await channel.declare_queue('updated_inventory_queue')

    async def callback(message):
        try:
            request_data_str = message.body.decode()
            message_data = json.loads(request_data_str)
            request = RequestItem(**message_data['request'])
            #print(f"Received UPDATED_INVENTORY event with request: {request}")
            await deliver_order(request)

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
    asyncio.run(inventory_consumer())