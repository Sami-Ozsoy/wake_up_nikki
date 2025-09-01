from smolagents import CodeAgent, Tool, OpenAIModel
from utils.helpers import get_llm
from utils.tools import (
    search_fm130_commands
)
from typing import Dict, Any
from config import OPENAI_API_KEY

class SearchFM130CommandsTool(Tool):
    """SmolAgents Tool: RAG'den FM130 bilgilerini getirir."""
    name = "search_fm130_commands"
    description = (
        "FM130/FMB Teltonika cihaz komut ve parametrelerini arar. "
        "Bu aracı SADECE kullanıcı sorusu cihaz komutları/parametreleriyle ilgiliyse kullan; "
        "genel sohbet veya cihaz dışı konularda bu aracı KULLANMA."
    )
    output_type = "any"
    inputs = {
        "query": {
            "type": "string",
            "description": "Kullanıcı sorgusu veya anahtar kelimeler"
        }
    }
    outputs = {
        "results": {
            "type": "array",
            "items": {"type": "object"},
            "description": "En alakalı komutlar ve metadataları"
        }
    }

    def forward(self, query: str):
        return search_fm130_commands(query)

class FM130SmolAgent:
    """FM130 komutları için SmolAgent implementasyonu"""
    
    def __init__(self):
        self.llm = get_llm()
        # SmolAgents için uygun model nesnesi
        self.model = OpenAIModel(model_id="gpt-4o-mini", api_key=OPENAI_API_KEY)

        # Model tabanlı yönlendirme talimatı (tool kullanım kararı modele bırakılır)
        self.system_prompt = (
            "Senin adın Niki. Türkçe ve doğal yanıt ver.\n"
            "- Eğer soru FM130/FMB/Teltonika cihaz komutları veya parametreleriyle ilgiliyse,\n"
            "  yalnızca o zaman 'search_fm130_commands' aracını KULLAN ve sonucu açıkla, SMS formatı ver.\n"
            "- Eğer soru cihaz-dışı/genel sohbet/gündelik konu ise HİÇBİR aracı KULLANMA,\n"
            "  kısa ve doğal bir cevap ver.\n"
            "- Araç kullanımına anahtar kelimeyle değil, sorunun niyetiyle karar ver."
        )
        
        # Yalnızca tek bir tool tanımla: RAG'den FM130 bilgilerini getirir
        self.tools = [SearchFM130CommandsTool()]
        
        # SmolAgent oluştur
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            name="FM130_Expert",
            description="FM130 cihaz komutları ve konfigürasyon uzmanı",
            max_steps=10
        )

    def _format_history(self, chat_history: Any) -> str:
        try:
            if not chat_history:
                return ""
            parts = []
            for user_turn, assistant_turn in chat_history[-5:]:
                parts.append(f"Kullanıcı: {user_turn}\nAsistan: {assistant_turn}")
            return "\n\n".join(parts)
        except Exception:
            return ""

    def _should_use_tool(self, message: str) -> bool:
        """Model tabanlı yönlendirme: Tool kullanılsın mı?"""
        try:
            judge_prompt = (
                "Soru FM130/FMB/Teltonika CİHAZ komutları veya parametreleriyle ilgili mi?\n"
                "Sadece 'YES' ya da 'NO' yaz. Başka bir şey yazma.\n\n"
                f"Soru: {message}"
            )
            resp = self.llm.invoke(judge_prompt)
            text = (resp.content if hasattr(resp, "content") else str(resp)).strip().lower()
            return text.startswith("y")  # yes -> tool kullan
        except Exception:
            return False

    def chat(self, message: str, chat_history: Any = None) -> str:
        """    
        Args:
            message: Kullanıcı mesajı
            
        Returns:
            str: Agent yanıtı
        """
        try:
            # 1) Model tabanlı niyet sınıflandırma: Tool gerekli mi?
            if not self._should_use_tool(message):
                # Genel sohbet: doğal kısa yanıt, CodeAgent'a girme → gereksiz adımlar yok
                natural_prompt = (
                    "Kısa ve doğal bir Türkçe selamlama/yanıt ver. \n\n"
                    f"Kullanıcı: {message}\nYanıt:"
                )
                resp = self.llm.invoke(natural_prompt)
                return resp.content if hasattr(resp, "content") else str(resp)

            # 2) Tool kullanılacaksa, CodeAgent'a sadece kullanıcı mesajını ver
            # (CodeAgent kendi yönlendirme şablonunu kullanır)
            response = self.agent.run(message)
            print("chat içinde response--->>>", response)
            return response
        except Exception as e:
            print(f"SmolAgent hatası: {e}")
            return f"❌ Agent hatası: {str(e)}"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Agent bilgilerini döndür"""
        return {
            'name': 'FM130 SmolAgent',
            'type': 'smolagents',
            'tools': ['search_fm130_commands'],
            'description': 'FM130 komutları için hafif ve hızlı agent'
        } 