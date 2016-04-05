import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = {
    'drivername': 'mysql',
    'host': '127.0.0.1',
    'port': '3306',
    'username': os.environ['DB_USERNAME'],
    'password': os.environ['DB_PASSWORD'],
    'database': 'ecom_products',
}

SHOP = {
	'name': os.environ['SHOP_NAME'],
}