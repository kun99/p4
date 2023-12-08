from dotenv import load_dotenv
import os
import aiomysql
import asyncio

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

async def connect():
    pool = await aiomysql.create_pool(
        host=MYSQL_HOST,
        user='root',
        password = MYSQL_ROOT_PASSWORD,
        db=MYSQL_DB,
        loop=asyncio.get_event_loop()
    )
    return pool

async def initialize():
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                credits INT
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                user VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                order_id INT
            );
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                quantity INT
            );
            INSERT IGNORE INTO inventory (name, quantity)
                VALUES ('tokens', 100);
            CREATE TABLE IF NOT EXISTS deliveries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                order_id INT,
                payment_id INT
            );
            """
            await cursor.execute(query)
            await conn.commit()
    pool.close()
    await pool.wait_closed()

async def create_user(name):
    print("HERE")
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "INSERT INTO users (name, credits) VALUES (%s, %s);"
            await cursor.execute(query, (name, 100,))
            created_id = cursor.lastrowid
            await conn.commit()
    pool.close()
    await pool.wait_closed()
    print('User created with id {:d}'.format(created_id))
    return created_id

async def get_user(name):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "SELECT * FROM users WHERE `name` = %s;"
            await cursor.execute(query, (name,))
            result = await cursor.fetchone()
    pool.close()
    await pool.wait_closed()
    return result

async def update_user_credits(name, user_id, new_credits):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "UPDATE users SET credits = %s WHERE id = %s;"
            await cursor.execute(query, (new_credits, user_id,))
            query = "SELECT * FROM users WHERE `name` = %s;"
            await cursor.execute(query, (name,))
            result = await cursor.fetchone()
            await conn.commit()
    pool.close()
    await pool.wait_closed()
    return result
    
async def delete_user(user_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "DELETE FROM users WHERE id = %s;"
            await cursor.execute(query, (user_id,))
            await conn.commit()
    pool.close()
    await pool.wait_closed()

#order

async def create_order(id, name):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "INSERT INTO orders (user_id, user) VALUES (%s, %s);"
            await cursor.execute(query, (id, name))
            created_id = cursor.lastrowid
            await conn.commit()
    pool.close()
    await pool.wait_closed()
    print('Order created with id {:d}'.format(created_id))
    return created_id

async def get_order(order_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "SELECT * FROM orders WHERE id = %s;"
            await cursor.execute(query, (order_id,))
            result = await cursor.fetchone()
    pool.close()
    await pool.wait_closed()
    return result

async def delete_order(order_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "DELETE FROM orders WHERE id = %s;"
            await cursor.execute(query, (order_id,))
            await conn.commit()
    pool.close()
    await pool.wait_closed()

# payment

async def create_payment(user_id, order_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "INSERT INTO payments (user_id, order_id) VALUES (%s, %s);"
            await cursor.execute(query, (user_id, order_id,))
            created_id = cursor.lastrowid
            await conn.commit()
    pool.close()
    await pool.wait_closed()
    print('Payment created with id {:d}'.format(created_id))
    return created_id

async def get_payment(payment_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "SELECT * FROM payments WHERE id = %s;"
            await cursor.execute(query, (payment_id,))
            result = await cursor.fetchone()
    pool.close()
    await pool.wait_closed()
    return result

async def delete_payment(payment_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "DELETE FROM payments WHERE id = %s;"
            await cursor.execute(query, (payment_id,))
            await conn.commit()
    pool.close()
    await pool.wait_closed()

# inventory

async def create_inventory(name, quantity):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "INSERT INTO inventory (name, quantity) VALUES (%s, %s);"
            await cursor.execute(query, (name, quantity,))
            await conn.commit()
    pool.close()
    await pool.wait_closed()

async def get_inventory(name):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "SELECT * FROM inventory WHERE `name` = %s;"
            await cursor.execute(query, (name,))
            result = await cursor.fetchone()
    pool.close()
    await pool.wait_closed()
    print(str(result))
    return result

async def update_inventory_quantity(id, new_quantity):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "UPDATE inventory SET quantity = %s WHERE id = %s;"
            await cursor.execute(query, (new_quantity, id,))
            await conn.commit()
    pool.close()
    await pool.wait_closed()

async def delete_inventory(inventory_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "DELETE FROM inventory WHERE id = %s;"
            await cursor.execute(query, (inventory_id,))
            await conn.commit()
    pool.close()
    await pool.wait_closed()

# delivery

async def create_delivery(user_id, order_id, payment_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "INSERT INTO deliveries (user_id, order_id, payment_id) VALUES (%s, %s, %s);"
            await cursor.execute(query, (user_id, order_id, payment_id))
            created_id = cursor.lastrowid
            await conn.commit()
    pool.close()
    await pool.wait_closed()
    return created_id

async def get_delivery(delivery_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "SELECT * FROM deliveries WHERE id = %s;"
            await cursor.execute(query, (delivery_id,))
            result = await cursor.fetchone()
    pool.close()
    await pool.wait_closed()
    return result

async def delete_delivery(delivery_id):
    pool = await connect()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = "DELETE FROM deliveries WHERE id = %s;"
            await cursor.execute(query, (delivery_id,))
            await conn.commit()
    pool.close()
    await pool.wait_closed()
    
if __name__ == "__main__":
    initialize()