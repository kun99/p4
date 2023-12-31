from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import aio_pika
import asyncio
import os
import json
from model.base_model import RequestItem
# from opentelemetry import trace
# from opentelemetry.exporter.jaeger import JaegerSpanExporter
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
# from opentelemetry.instrumentation.aiohttp import AioHTTPInstrumentor

app = FastAPI()

# trace.set_tracer_provider(TracerProvider())
# tracer = trace.get_tracer(__name__)
# span_processor = BatchExportSpanProcessor(JaegerSpanExporter(service_name="name"))
# trace.get_tracer_provider().add_span_processor(span_processor)

# FastAPIInstrumentor.instrument_app(app)
# AioHTTPInstrumentor.instrument()

load_dotenv()
host = os.getenv("HOST")
port = int(os.getenv("PORT"))

stop_listener = False
returning = "UNKNOWN"

@app.post("/buy_token")
async def buy_token(request: RequestItem):
    try:
        global returning, stop_listener
        stop_listener = False
        
        task_event_listener = asyncio.create_task(event_listener())
        task_start_transaction = asyncio.create_task(start_transaction(request))
        #await asyncio.gather(task_event_listener, task_start_transaction)
        done, pending = await asyncio.wait(
            [task_event_listener, task_start_transaction],
            timeout=30,
            return_when=asyncio.ALL_COMPLETED
        )
        if pending:
            raise asyncio.TimeoutError()
        
        message = returning
        returning = "UNKNOWN"
        if message == "SUCCESS":
            return JSONResponse(content={"message": message}, status_code=200)
        else:
            return JSONResponse(content={"message": message}, status_code=500)
    except asyncio.TimeoutError:
        return JSONResponse(content={"message": "TIMEOUT"}, status_code=504)
    except Exception as e:
        print(e)
        return returning

async def start_transaction(request: RequestItem):
    global stop_listener
    if request.action == "failAtStart":
        stop_listener = True
        print("Failed at start")
        return
    elif request.action == "timeout":
        await asyncio.sleep(35)
        stop_listener = True
        return
    print("STARTING TRANSACTION")
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange("direct_event", aio_pika.ExchangeType.DIRECT)

    message_data = {'request': request.dict(), 'event_name': 'TRANSACTION_STARTED'}
    message_body = json.dumps(message_data)
    await exchange.publish(
        aio_pika.Message(body=message_body.encode()),
        routing_key='TRANSACTION_STARTED',
    )
    await connection.close()
    
async def process_event(event_type):
    #compensating transactions coming soon ~ in 5 hrs or so :)
    print(f"RECEIVED EVENT {event_type}")
    global stop_listener, returning
    publishing_event = ''
    if event_type == 'ORDER_CREATED':
        publishing_event = 'START_PAYMENT'   
    elif event_type == 'ORDER_FAILED':
        stop_listener = True
    elif event_type == 'PAYMENT_PROCESSED':
        publishing_event = 'START_INVENTORY'   
    elif event_type == 'PAYMENT_FAILED':
        publishing_event = 'ROLLBACK_ORDER'
    elif event_type == 'UPDATED_INVENTORY':
        publishing_event = 'START_DELIVERY'    
    elif event_type == 'INVENTORY_FAILED':
        publishing_event = 'ROLLBACK_PAYMENT' 
    elif event_type == 'DELIVERED_ORDER':
        returning = "SUCCESS"
        stop_listener = True
    elif event_type == 'FAILED_DELIVERY':
        publishing_event = 'ROLLBACK_INVENTORY' 
    elif event_type == 'INSUFFICIENT_FUNDS':
        publishing_event = 'ROLLBACK_ORDER' 
        returning = "INSUFFICIENT_FUNDS"
    elif event_type == 'OUT_OF_STOCK':
        publishing_event = 'ROLLBACK_PAYMENT' 
        returning = "OUT_OF_STOCK"
    return publishing_event
    
async def publish_event(publishing_event, request: RequestItem):
    connection = await aio_pika.connect_robust(
        host=host,
        port=port,
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange("direct_event", aio_pika.ExchangeType.DIRECT)

    message_data = {'request': request.model_dump(), 'event_name': publishing_event}
    message_body = json.dumps(message_data)
    print(publishing_event)
    await exchange.publish(
        aio_pika.Message(body=message_body.encode()),
        routing_key=publishing_event,
    )
    await connection.close()
    
async def event_listener():
    connection = None
    while not stop_listener:
        try: 
            connection = await aio_pika.connect_robust(
                host=host,
                port=port,
            )
            channel = await connection.channel()
            queue = await channel.declare_queue('')
            exchange = await channel.declare_exchange("direct_event", type=aio_pika.ExchangeType.DIRECT)

            await queue.bind(exchange=exchange, routing_key="ORDER_CREATED")
            await queue.bind(exchange=exchange, routing_key="ORDER_FAILED")
            await queue.bind(exchange=exchange, routing_key="PAYMENT_PROCESSED")
            await queue.bind(exchange=exchange, routing_key="PAYMENT_FAILED")
            await queue.bind(exchange=exchange, routing_key="UPDATED_INVENTORY")
            await queue.bind(exchange=exchange, routing_key="INVENTORY_FAILED")
            await queue.bind(exchange=exchange, routing_key="DELIVERED_ORDER")
            await queue.bind(exchange=exchange, routing_key="FAILED_DELIVERY")
            await queue.bind(exchange=exchange, routing_key="INSUFFICIENT_FUNDS")
            await queue.bind(exchange=exchange, routing_key="OUT_OF_STOCK")
        
            async def callback(message):
                try:
                    request_data_str = message.body.decode()
                    message_data = json.loads(request_data_str)
                    event_type = message.routing_key
                    request = RequestItem(**message_data['request'])
                    event = await process_event(event_type)
                    await publish_event(event, request)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                await message.ack()

            await queue.consume(callback)
            await asyncio.sleep(1)
            
        except Exception as e:
            print(e)
            print("Couldn't be set up to receive any messages")
        finally:
            if connection is not None and not connection.is_closed and queue is not None:
                await connection.close()
    
# request looks like this
# {
#   "action": "placeOrder",
#   "data": {
#     "name": "user",
#   },
#   "failures": {
#      "orderFailure": "cancelOrder",
#      "paymentFailure": "cancelPayment",
#      "emptyInventory": "reverseInventory",
#      "deliveryFailure": "cancelDelivery",
#      "databaseFailure": "cancelProcess",
#      "insufficientFunds": "cancelPayment",
#      "inventoryFailure": "reverseInventory",
#   }    
# }