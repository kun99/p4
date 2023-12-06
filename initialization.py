from db.db import initialize_users, initialize_orders, initialize_payments, initialize_inventory, initialize_inventory, initialize_delivery

def initialize_tables():
    if not initialize_users():
        return False
    if not initialize_orders():
        return False
    if not initialize_payments():
        return False
    if not initialize_inventory():
        return False
    if not initialize_delivery():
        return False
    return True