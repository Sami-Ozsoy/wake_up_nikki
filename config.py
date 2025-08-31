import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') 