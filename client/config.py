from dotenv import load_dotenv
import os

# Константы с credentials
MASTER_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "admin",
    "password": "admin123",
    "dbname": "test_db"
}

REPLICA_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "admin",
    "password": "admin123",
    "dbname": "test_db"
}


load_dotenv()

# Конфигурация для мастера
MASTER_CONFIG = {
    'host': os.getenv('MASTER_HOST'),
    'port': int(os.getenv('MASTER_PORT', '5432')),
    'user': os.getenv('MASTER_USER'),
    'password': os.getenv('MASTER_PASSWORD'),
    'dbname': os.getenv('MASTER_DB'),
}

# Конфигурация для реплики
REPLICA_CONFIG = {
    'host': os.getenv('REPLICA_HOST'),
    'port': int(os.getenv('REPLICA_PORT', '5433')),
    'user': os.getenv('REPLICA_USER'),
    'password': os.getenv('REPLICA_PASSWORD'),
    'dbname': os.getenv('REPLICA_DB'),
}