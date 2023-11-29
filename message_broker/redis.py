from fastapi import FastAPI, HTTPException, WebSocket
import aioredis

app = FastAPI()
redis = aioredis.from_url("redis://localhost", decode_responses=True)

@app.post("/create_order/{order_id}")
async def create_order(order_id: int):
    # Business logic for order creation
    await redis.publish("order_created", order_id)
    return {"status": "Order created successfully"}

# WebSocket example for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await redis.publish("websocket_channel", data)