from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain_ollama import OllamaLLM

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
def get_llm():
    """OpenAI LLM istemcisini döndür"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0.7
    )

# def get_llm():
#     """Ollama LLM istemcisini döndür"""
#     return OllamaLLM(
#         model="mistral:7b-instruct",  # veya "mistral:7b-instruct"  # Tekrarları azalt
#         num_ctx=8192, 
#         base_url="http://localhost:11434"  # Ollama'nın varsayılan URL'i
#     )

# def get_llm():
#     """LM Studio LLM istemcisini döndür"""
#     return OllamaLLM(
#         model="mistral:7b",
#         temperature=0.7,
#         base_url="http://localhost:1234/v1"  # LM Studio'nun API endpoint'i
#     )