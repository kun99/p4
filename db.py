import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

def connect():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    
def initialize_users():
    conn = connect()
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        credits INT
    )
    """
    cursor.execute(query)
    conn.close()

def create_user(name):
    conn = connect()
    cursor = conn.cursor()
    query = "INSERT INTO users (name, credits) VALUES (%s, %s)"
    cursor.execute(query, (name, credits))
    conn.commit()
    created_id = cursor.lastrowid
    conn.close()
    return created_id
    
def get_user(name):
    conn = connect()
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE name = {name}"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def update_user_credits(user_id, new_credits):
    conn = connect()
    cursor = conn.cursor()
    query = "UPDATE users SET credits = %s WHERE id = %s"
    cursor.execute(query, (new_credits, user_id))
    conn.commit()
    conn.close()
    
initialize_users()

#order

def initialize_orders():
    conn = connect()
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        user VARCHAR(255),
    )
    """
    cursor.execute(query)
    conn.close()

def create_order(id, name):
    conn = connect()
    cursor = conn.cursor()
    query = "INSERT INTO orders (user_id, user) VALUES (%s, %s)"
    cursor.execute(query, (id, name))
    conn.commit()
    created_id = cursor.lastrowid
    conn.close()
    return created_id
    
def get_order(order_id):
    conn = connect()
    cursor = conn.cursor()
    query = f"SELECT * FROM orders WHERE id = {order_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def delete_order(order_id):
    conn = connect()
    cursor = conn.cursor()
    query = f"DELETE FROM orders WHERE id = {order_id}"
    cursor.execute(query)
    conn.commit()
    conn.close()
    
#payment

def initialize_payments():
    conn = connect()
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS payments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        order_id INT
    )
    """
    cursor.execute(query)
    conn.close()
    
def create_payment(user_id, order_id):
    conn = connect()
    cursor = conn.cursor()
    query = "INSERT INTO payments (user_id, order_id) VALUES (%s, %s)"
    cursor.execute(query, (user_id, order_id))
    conn.commit()
    created_id = cursor.lastrowid
    conn.close()
    return created_id
    
def get_payment(payment_id):
    conn = connect()
    cursor = conn.cursor()
    query = f"SELECT * FROM payments WHERE id = {payment_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def delete_payment(payment_id):
    conn = connect()
    cursor = conn.cursor()
    query = f"DELETE FROM payments WHERE id = {payment_id}"
    cursor.execute(query)
    conn.commit()
    conn.close()

#inventory

def initialize_inventory():
    conn = connect()
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS inventory (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        quantity INT
    );
    INSERT INTO inventory (name) VALUES ('tokens', 100);
    """
    cursor.execute(query)
    conn.close()
    
def create_inventory(name, quantity):
    conn = connect()
    cursor = conn.cursor()
    query = "INSERT INTO inventory (name, quantity) VALUES (%s, %s)"
    cursor.execute(query, (name, quantity))
    conn.commit()
    conn.close()
    
def get_inventory(name):
    conn = connect()
    cursor = conn.cursor()
    query = f"SELECT * FROM inventory WHERE name = {name}"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def update_inventory_quantity(name, new_quantity):
    conn = connect()
    cursor = conn.cursor()
    query = "UPDATE users SET quantity = %s WHERE name = %s"
    cursor.execute(query, (new_quantity, name))
    conn.commit()
    conn.close()

def delete_inventory(inventory_id):
    conn = connect()
    cursor = conn.cursor()
    query = f"DELETE FROM inventory WHERE id = {inventory_id}"
    cursor.execute(query)
    conn.commit()
    conn.close()

#delivery

def initialize_delivery():
    conn = connect()
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS deliveries (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        order_id INT,
        payment_id INT,
        inventory VARCHAR(255)
    )
    """
    cursor.execute(query)
    conn.close()
    
def create_delivery(user_id, order_id, payment_id, inventory):
    conn = connect()
    cursor = conn.cursor()
    query = "INSERT INTO deliveries (user_id, order_id, payment_id, inventory) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, order_id, payment_id, inventory))
    conn.commit()
    conn.close()
    
def get_delivery(delivery_id):
    conn = connect()
    cursor = conn.cursor()
    query = f"DELETE * FROM deliveries WHERE id = {delivery_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def delete_delivery(delivery_id):
    conn = connect()
    cursor = conn.cursor()
    query = f"DELETE FROM deliveries WHERE id = {delivery_id}"
    cursor.execute(query)
    conn.commit()
    conn.close()