from smolagents import CodeAgent, Tool
from utils.helpers import get_llm
from utils.tools import (
    search_fm130_commands,
    get_command_details,
    validate_parameters,
    create_configuration_plan,
    troubleshoot_fm130_issue
)
from typing import Dict, Any

class FM130SmolAgent:
    """FM130 komutları için SmolAgent implementasyonu"""
    
    def __init__(self):
        self.llm = get_llm()
        
        # Tools tanımla
        self.tools = [
            Tool(
                name="search_fm130_commands",
                func=search_fm130_commands,
                description="FM130 komutlarını vector store'da ara. Kullanıcı sorgusuna göre ilgili komutları bulur."
            ),
            Tool(
                name="get_command_details",
                func=get_command_details,
                description="Belirli bir FM130 komutunun detaylarını getirir. Komut adı verilmelidir."
            ),
            Tool(
                name="validate_parameters",
                func=validate_parameters,
                description="FM130 komut parametrelerini doğrular. Komut adı ve parametreler verilmelidir."
            ),
            Tool(
                name="create_configuration_plan",
                func=create_configuration_plan,
                description="FM130 konfigürasyon planı oluşturur. Kullanıcı gereksinimleri verilmelidir."
            ),
            Tool(
                name="troubleshoot_fm130_issue",
                func=troubleshoot_fm130_issue,
                description="FM130 sorunlarını teşhis eder ve çözüm önerir. Sorun açıklaması verilmelidir."
            )
        ]
        
        # SmolAgent oluştur
        self.agent = CodeAgent(
            tools=self.tools,
            llm=self.llm,
            name="FM130_Expert",
            description="FM130 cihaz komutları ve konfigürasyon uzmanı"
        )
    
    def chat(self, message: str) -> str:
        """
        Kullanıcı mesajına yanıt ver
        
        Args:
            message: Kullanıcı mesajı
            
        Returns:
            str: Agent yanıtı
        """
        try:
            # Agent'ı çalıştır
            response = self.agent.run(message)
            return response
        except Exception as e:
            print(f"SmolAgent hatası: {e}")
            return f"❌ Agent hatası: {str(e)}"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Agent bilgilerini döndür"""
        return {
            'name': 'FM130 SmolAgent',
            'type': 'smolagents',
            'tools': [tool.name for tool in self.tools],
            'description': 'FM130 komutları için hafif ve hızlı agent'
        } 