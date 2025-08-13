from typing import Dict, Any, Optional
from utils.agents.smol_agent import FM130SmolAgent
from utils.agents.langgraph_agent import FM130LangGraphAgent
from utils.helpers import get_llm
from utils.loaders import load_prompt
from vector.vector_store import VectorStore
from utils.formatter import format_llm_response, format_error_response, format_no_info_response
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

class AgentFactory:
    """FM130 agent'ları için factory sınıfı"""
    
    def __init__(self):
        self.agents = {}
        self.vector_store = VectorStore()
        self.llm = get_llm()
        
        # Traditional RAG için prompt
        prompt_text = load_prompt("prompts/main_prompt.txt")
        self.prompt = ChatPromptTemplate.from_template(prompt_text)
    
    def get_agent(self, agent_type: str = "rag"):
        """
        Belirtilen türde agent'ı döndür
        
        Args:
            agent_type: Agent türü ("rag", "smol", "langgraph")
            
        Returns:
            Agent instance
        """
        if agent_type not in self.agents:
            if agent_type == "smol":
                try:
                    self.agents[agent_type] = FM130SmolAgent()
                except Exception as e:
                    print(f"SmolAgent oluşturulamadı: {e}")
                    return self._create_fallback_agent()
                    
            elif agent_type == "langgraph":
                try:
                    self.agents[agent_type] = FM130LangGraphAgent()
                except Exception as e:
                    print(f"LangGraph Agent oluşturulamadı: {e}")
                    return self._create_fallback_agent()
                    
            elif agent_type == "rag":
                self.agents[agent_type] = self._create_rag_agent()
            else:
                print(f"Bilinmeyen agent türü: {agent_type}")
                return self._create_fallback_agent()
        
        return self.agents[agent_type]
    
    def _create_rag_agent(self):
        """Traditional RAG agent oluştur"""
        class RAGAgent:
            def __init__(self, factory):
                self.factory = factory
                self.vector_store = factory.vector_store
                self.llm = factory.llm
                self.prompt = factory.prompt
            
            def chat(self, message: str) -> str:
                """RAG tabanlı yanıt ver"""
                try:
                    # Vector context al
                    retriever = self.vector_store.get_retriever(k=6)
                    retrieved_docs = retriever.invoke(message)
                    
                    # Score'larla birlikte similarity search yap
                    docs_with_scores = self.vector_store.similarity_search_with_score(message, k=6)
                    
                    # Sadece yüksek score'lu dokümanları al (0.7+)
                    high_quality_docs = []
                    for doc, score in docs_with_scores:
                        if score > 0.7:
                            high_quality_docs.append(doc)
                    
                    if not high_quality_docs:
                        high_quality_docs = retrieved_docs
                    
                    docs_content = "\n\n".join([doc.page_content for doc in high_quality_docs])
                    
                    # Context hazırla
                    context_data = {
                        "question": message,
                        "context": f"{docs_content}\n\nKullanıcı: {message}"
                    }
                    
                    # Prompt'u formatla
                    formatted_prompt = self.prompt.format(**context_data)
                    
                    # LLM'den yanıt al
                    response = self.llm.invoke(formatted_prompt)
                    response_content = response.content if hasattr(response, 'content') else str(response)
                    
                    # Yanıtı formatla
                    formatted_response = format_llm_response(response_content)
                    
                    # Eğer yanıt çok kısaysa
                    if len(formatted_response.strip()) < 50:
                        return format_no_info_response()
                    
                    return formatted_response
                    
                except Exception as e:
                    print(f"RAG agent hatası: {e}")
                    return format_error_response(str(e))
            
            def get_agent_info(self) -> Dict[str, Any]:
                """Agent bilgilerini döndür"""
                return {
                    'name': 'FM130 RAG Agent',
                    'type': 'rag',
                    'description': 'Geleneksel RAG tabanlı FM130 komut yardımcısı'
                }
        
        return RAGAgent(self)
    
    def _create_fallback_agent(self):
        """Fallback agent oluştur (hata durumunda)"""
        class FallbackAgent:
            def __init__(self):
                self.llm = get_llm()
            
            def chat(self, message: str) -> str:
                """Basit fallback yanıt"""
                try:
                    prompt = f"""
                    FM130 cihazı hakkında soru: {message}
                    
                    Lütfen kullanıcıya yardımcı ol. Eğer FM130 komutları hakkında bilgin yoksa, 
                    bunu belirt ve genel yardım öner.
                    """
                    
                    response = self.llm.invoke(prompt)
                    return response.content if hasattr(response, 'content') else str(response)
                    
                except Exception as e:
                    return f"❌ Fallback agent hatası: {str(e)}"
            
            def get_agent_info(self) -> Dict[str, Any]:
                """Agent bilgilerini döndür"""
                return {
                    'name': 'FM130 Fallback Agent',
                    'type': 'fallback',
                    'description': 'Hata durumunda kullanılan basit agent'
                }
        
        return FallbackAgent()
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Mevcut agent'ların listesini döndür"""
        available = {}
        
        # RAG agent her zaman mevcut
        available["rag"] = {
            'name': 'FM130 RAG Agent',
            'type': 'rag',
            'description': 'Geleneksel RAG tabanlı FM130 komut yardımcısı',
            'status': 'available'
        }
        
        # SmolAgent kontrol et
        try:
            smol_agent = FM130SmolAgent()
            available["smol"] = smol_agent.get_agent_info()
            available["smol"]["status"] = "available"
        except Exception as e:
            available["smol"] = {
                'name': 'FM130 SmolAgent',
                'type': 'smol',
                'description': 'Hafif ve hızlı agent (kurulum gerekli)',
                'status': 'unavailable',
                'error': str(e)
            }
        
        # LangGraph agent kontrol et
        try:
            langgraph_agent = FM130LangGraphAgent()
            available["langgraph"] = langgraph_agent.get_agent_info()
            available["langgraph"]["status"] = "available"
        except Exception as e:
            available["langgraph"] = {
                'name': 'FM130 LangGraph Agent',
                'type': 'langgraph',
                'description': 'State machine tabanlı agent (kurulum gerekli)',
                'status': 'unavailable',
                'error': str(e)
            }
        
        return available
    
    def clear_agent_cache(self):
        """Agent cache'ini temizle"""
        self.agents.clear()
        print("Agent cache temizlendi") 