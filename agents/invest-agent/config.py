import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# AkShare 的请求走这个代理（本机 Clash）。设成空字符串就直连
AKSHARE_PROXY = os.getenv("AKSHARE_PROXY", "http://127.0.0.1:7897")
