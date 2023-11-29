from fastapi import FastAPI
from services import order, payment, inventory, delivery
from message_broker import redis_config

from message_broker import redis_config

app = FastAPI()

app.include_router(order.router)
app.include_router(payment.router)
app.include_router(inventory.router)
app.include_router(delivery.router)

redis_config.setup_redis(app)