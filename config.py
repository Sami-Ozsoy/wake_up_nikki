import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Neo4j Database URI
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password') 