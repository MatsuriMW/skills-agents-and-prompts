import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")