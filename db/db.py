import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

def connect():
    conn_without_db = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cursor = conn_without_db.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
    cursor.close()
    conn_without_db.close()
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    
def initialize_users():
    try:
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
        return True
    except Exception as e:
        print("Failed to initialize users")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def create_user(name):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "INSERT INTO users (name, credits) VALUES (%s, %s)"
        cursor.execute(query, (name, 100,))
        conn.commit()
        created_id = cursor.lastrowid
        print('User created with id {:d}'.format(created_id))
        return created_id
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
def get_user(name):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE name = %s"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        if result is None:
            return "NoUser"
        return result
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_user_credits(user_id, new_credits):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "UPDATE users SET credits = %s WHERE id = %s"
        cursor.execute(query, (new_credits, user_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
#order

def initialize_orders():
    try:
        conn = connect()
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            user VARCHAR(255)
        )
        """
        cursor.execute(query)
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def create_order(id, name):
    try: 
        conn = connect()
        cursor = conn.cursor()
        query = "INSERT INTO orders (user_id, user) VALUES (%s, %s)"
        cursor.execute(query, (id, name))
        conn.commit()
        created_id = cursor.lastrowid
        print('Order created with id {:d}'.format(created_id))
        return created_id
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
def get_order(order_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "SELECT * FROM orders WHERE id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_order(order_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "DELETE FROM orders WHERE id = %s"
        cursor.execute(query, (order_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
#payment

def initialize_payments():
    try:
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
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
def create_payment(user_id, order_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "INSERT INTO payments (user_id, order_id) VALUES (%s, %s)"
        cursor.execute(query, (user_id, order_id,))
        conn.commit()
        created_id = cursor.lastrowid
        print('Payment created with id {:d}'.format(created_id))
        return created_id
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
def get_payment(payment_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "SELECT * FROM payments WHERE id = %s"
        cursor.execute(query, (payment_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_payment(payment_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "DELETE FROM payments WHERE id = %s"
        cursor.execute(query, (payment_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#inventory

def initialize_inventory():
    try:
        conn = connect()
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            quantity INT
        );
        INSERT IGNORE INTO inventory (name, quantity)
        VALUES ('tokens', 100);
        """
        cursor.execute(query)
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
def create_inventory(name, quantity):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "INSERT INTO inventory (name, quantity) VALUES (%s, %s)"
        cursor.execute(query, (name, quantity,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
def get_inventory(name):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "SELECT * FROM inventory WHERE name = %s"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_inventory_quantity(name, new_quantity):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "UPDATE inventory SET quantity = %s WHERE name = %s"
        cursor.execute(query, (new_quantity, name,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_inventory(inventory_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "DELETE FROM inventory WHERE id = %s"
        cursor.execute(query, (inventory_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

#delivery

def initialize_delivery():
    try:
        conn = connect()
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS deliveries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            order_id INT,
            payment_id INT
        )
        """
        cursor.execute(query)
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
def create_delivery(user_id, order_id, payment_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "INSERT INTO deliveries (user_id, order_id, payment_id) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, order_id, payment_id))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
def get_delivery(delivery_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "SELECT * FROM deliveries WHERE id = %s"
        cursor.execute(query, (delivery_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_delivery(delivery_id):
    try:
        conn = connect()
        cursor = conn.cursor()
        query = "DELETE FROM deliveries WHERE id = %s"
        cursor.execute(query, (delivery_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
