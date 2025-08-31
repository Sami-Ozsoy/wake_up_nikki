from typing import Dict, Any
from utils.agents.smol_agent import FM130SmolAgent
from utils.helpers import get_llm

class AgentFactory:
    """FM130 agent'ları için factory sınıfı (yalnızca SmolAgent)."""

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.llm = get_llm()

    def get_agent(self, _agent_type: str = "smol"):
        """
        Yalnızca SmolAgent döndürür. Diğer tüm türler SmolAgent'a yönlendirilir.
        """
        if "smol" not in self.agents:
            try:
                self.agents["smol"] = FM130SmolAgent()
            except Exception as e:
                print(f"SmolAgent oluşturulamadı: {e}")
                return self._create_fallback_agent()

        return self.agents["smol"]
    
    # RAG kaldırıldı
    
    def _create_fallback_agent(self):
        """Fallback agent oluştur (hata durumunda)"""
        class FallbackAgent:
            def __init__(self):
                self.llm = get_llm()
            
            def chat(self, message: str, chat_history: Any = None) -> str:
                """Basit fallback yanıt"""
                try:
                    prompt = f"""
                    FM130 cihazı hakkında soru: {message}
                    
                    Lütfen kullanıcıya yardımcı ol. Eğer FM130 komutları hakkında bilgin yoksa, 
                    bunu belirt ve genel yardım öner.

                    Chat geçmişi:
                    {chat_history}
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
    
    def get_available_agents(self) -> Dict[str, Any]:
        """Mevcut agent'ların listesini döndür (yalnızca SmolAgent)."""
        available: Dict[str, Any] = {}
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
        return available
    
    def clear_agent_cache(self):
        """Agent cache'ini temizle"""
        self.agents.clear()
        print("Agent cache temizlendi") 