from pyrogram.client import Client
from dotenv import load_dotenv
import os


load_dotenv()
PARSER_ID = os.getenv("PARSER_ID")
PARSER_HASH = os.getenv("PARSER_HASH")
PHONE_NUM = os.getenv("PHONE_NUM")


with Client(
    "Parser", PARSER_ID, PARSER_HASH
) as app:
    print(app.export_session_string())