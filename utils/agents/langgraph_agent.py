from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from utils.helpers import get_llm
from utils.tools import (
    search_fm130_commands,
    get_command_details,
    validate_parameters,
    create_configuration_plan,
    troubleshoot_fm130_issue
)

class FM130State(TypedDict):
    """FM130 agent state şeması"""
    question: str
    commands: List[Dict[str, Any]]
    command_details: Dict[str, Any]
    validation_result: Dict[str, Any]
    configuration_plan: Dict[str, Any]
    troubleshooting_result: Dict[str, Any]
    answer: str
    error: str

class FM130LangGraphAgent:
    """FM130 komutları için LangGraph implementasyonu"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = MemorySaver()
        self.workflow = self._create_workflow()
    
    def _analyze_intent(self, state: FM130State) -> FM130State:
        """Kullanıcı niyetini analiz et"""
        try:
            question = state["question"]
            
            # Basit intent analizi
            if any(word in question.lower() for word in ['batarya', 'battery', 'power']):
                intent = "battery_check"
            elif any(word in question.lower() for word in ['gprs', 'internet', 'bağlantı']):
                intent = "connectivity"
            elif any(word in question.lower() for word in ['sms', 'mesaj']):
                intent = "communication"
            elif any(word in question.lower() for word in ['ayarla', 'set', 'konfigürasyon']):
                intent = "configuration"
            elif any(word in question.lower() for word in ['sorun', 'hata', 'problem']):
                intent = "troubleshooting"
            else:
                intent = "general_query"
            
            state["intent"] = intent
            return state
            
        except Exception as e:
            state["error"] = f"Intent analizi hatası: {str(e)}"
            return state
    
    def _retrieve_commands(self, state: FM130State) -> FM130State:
        """İlgili komutları getir"""
        try:
            question = state["question"]
            commands = search_fm130_commands(question)
            state["commands"] = commands
            return state
            
        except Exception as e:
            state["error"] = f"Komut arama hatası: {str(e)}"
            return state
    
    def _get_command_details(self, state: FM130State) -> FM130State:
        """Komut detaylarını getir"""
        try:
            if state.get("commands"):
                # İlk komutu detaylandır
                first_command = state["commands"][0]
                command_name = first_command.get('content', '').split()[0] if first_command.get('content') else ''
                
                if command_name:
                    details = get_command_details(command_name)
                    state["command_details"] = details
            
            return state
            
        except Exception as e:
            state["error"] = f"Komut detay hatası: {str(e)}"
            return state
    
    def _validate_if_needed(self, state: FM130State) -> FM130State:
        """Gerekirse parametre doğrulaması yap"""
        try:
            intent = state.get("intent")
            
            if intent in ["configuration", "set"]:
                # Basit doğrulama (gerçek projede daha gelişmiş olabilir)
                validation_result = {
                    'valid': True,
                    'message': 'Konfigürasyon için hazır'
                }
                state["validation_result"] = validation_result
            
            return state
            
        except Exception as e:
            state["error"] = f"Doğrulama hatası: {str(e)}"
            return state
    
    def _create_config_plan_if_needed(self, state: FM130State) -> FM130State:
        """Gerekirse konfigürasyon planı oluştur"""
        try:
            intent = state.get("intent")
            
            if intent in ["configuration", "set"]:
                plan = create_configuration_plan(state["question"])
                state["configuration_plan"] = plan
            
            return state
            
        except Exception as e:
            state["error"] = f"Plan oluşturma hatası: {str(e)}"
            return state
    
    def _troubleshoot_if_needed(self, state: FM130State) -> FM130State:
        """Gerekirse sorun giderme yap"""
        try:
            intent = state.get("intent")
            
            if intent == "troubleshooting":
                troubleshooting = troubleshoot_fm130_issue(state["question"])
                state["troubleshooting_result"] = troubleshooting
            
            return state
            
        except Exception as e:
            state["error"] = f"Sorun giderme hatası: {str(e)}"
            return state
    
    def _generate_response(self, state: FM130State) -> FM130State:
        """Final yanıtı oluştur"""
        try:
            if state.get("error"):
                state["answer"] = f"❌ Hata: {state['error']}"
                return state
            
            # Context'i hazırla
            context_parts = []
            
            if state.get("commands"):
                context_parts.append(f"Bulunan komutlar: {len(state['commands'])} adet")
            
            if state.get("command_details"):
                context_parts.append(f"Komut detayları: {state['command_details'].get('name', 'N/A')}")
            
            if state.get("configuration_plan"):
                context_parts.append(f"Konfigürasyon planı hazır")
            
            if state.get("troubleshooting_result"):
                context_parts.append(f"Sorun giderme tamamlandı")
            
            context = "\n".join(context_parts) if context_parts else "Genel sorgu"
            
            # LLM'den yanıt al
            prompt = f"""
            FM130 cihazı hakkında soru: {state['question']}
            
            Context: {context}
            
            Lütfen kullanıcıya yardımcı ol ve FM130 komutları hakkında detaylı bilgi ver.
            """
            
            response = self.llm.invoke(prompt)
            state["answer"] = response.content if hasattr(response, 'content') else str(response)
            
            return state
            
        except Exception as e:
            state["answer"] = f"❌ Yanıt oluşturma hatası: {str(e)}"
            return state
    
    def _create_workflow(self):
        """LangGraph workflow'unu oluştur"""
        workflow = StateGraph(FM130State)
        
        # Node'ları ekle
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("retrieve_commands", self._retrieve_commands)
        workflow.add_node("get_command_details", self._get_command_details)
        workflow.add_node("validate_if_needed", self._validate_if_needed)
        workflow.add_node("create_config_plan_if_needed", self._create_config_plan_if_needed)
        workflow.add_node("troubleshoot_if_needed", self._troubleshoot_if_needed)
        workflow.add_node("generate_response", self._generate_response)
        
        # Flow'u tanımla
        workflow.add_edge("analyze_intent", "retrieve_commands")
        workflow.add_edge("retrieve_commands", "get_command_details")
        workflow.add_edge("get_command_details", "validate_if_needed")
        workflow.add_edge("validate_if_needed", "create_config_plan_if_needed")
        workflow.add_edge("create_config_plan_if_needed", "troubleshoot_if_needed")
        workflow.add_edge("troubleshoot_if_needed", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def chat(self, message: str) -> str:
        """
        Kullanıcı mesajına yanıt ver
        
        Args:
            message: Kullanıcı mesajı
            
        Returns:
            str: Agent yanıtı
        """
        try:
            # Initial state
            initial_state = {
                "question": message,
                "commands": [],
                "command_details": {},
                "validation_result": {},
                "configuration_plan": {},
                "troubleshooting_result": {},
                "answer": "",
                "error": ""
            }
            
            # Workflow'u çalıştır
            result = self.workflow.invoke(initial_state)
            
            return result.get("answer", "❌ Yanıt alınamadı")
            
        except Exception as e:
            print(f"LangGraph hatası: {e}")
            return f"❌ LangGraph hatası: {str(e)}"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Agent bilgilerini döndür"""
        return {
            'name': 'FM130 LangGraph Agent',
            'type': 'langgraph',
            'description': 'FM130 komutları için state machine tabanlı agent',
            'workflow_nodes': [
                'analyze_intent',
                'retrieve_commands', 
                'get_command_details',
                'validate_if_needed',
                'create_config_plan_if_needed',
                'troubleshoot_if_needed',
                'generate_response'
            ]
        } 