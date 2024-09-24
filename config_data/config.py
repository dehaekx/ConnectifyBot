import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
HOST = os.getenv("HOST")
DATABASE = os.getenv('DATABASE')
USER = os.getenv('USER')
PORT = os.getenv('PORT')
PASSWORD = os.getenv('PASSWORD')
DB_URI = os.getenv('DATABASE_URL')
admin_id = os.getenv("ADMIN_ID")


chat_for_save_file_id = '961570363'
