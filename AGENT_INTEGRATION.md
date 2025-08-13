# 🤖 FM130 Agent Entegrasyonu

Bu dokümantasyon, FM130 projesine eklenen LLM agent'larının nasıl kullanılacağını açıklar.

## 🚀 Eklenen Özellikler

### 1. **Çoklu Agent Desteği**
- **RAG Agent**: Geleneksel RAG tabanlı yaklaşım
- **SmolAgent**: Hafif ve hızlı agent
- **LangGraph Agent**: State machine tabanlı gelişmiş agent

### 2. **Ortak Tool Sistemi**
Tüm agent'lar aynı domain-specific tools'ları kullanır:
- `search_fm130_commands`: FM130 komutlarını ara
- `get_command_details`: Komut detaylarını getir
- `validate_parameters`: Parametreleri doğrula
- `create_configuration_plan`: Konfigürasyon planı oluştur
- `troubleshoot_fm130_issue`: Sorun giderme

### 3. **Agent Factory Pattern**
Merkezi agent yönetimi ve otomatik fallback sistemi.

## 📁 Dosya Yapısı

```
utils/
├── agents/
│   ├── __init__.py
│   ├── smol_agent.py          # SmolAgent implementasyonu
│   ├── langgraph_agent.py     # LangGraph implementasyonu
│   └── agent_factory.py       # Agent factory ve yönetimi
├── tools.py                   # Ortak domain tools
└── helpers.py                 # LLM yardımcıları
```

## 🛠️ Kurulum

### 1. **Dependencies Ekle**
```bash
pip install smolagents langgraph pydantic
```

### 2. **Environment Variables**
```bash
# .env dosyası
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. **Test Et**
```bash
python test_agents.py
```

## 🎯 Kullanım

### **Flask Uygulaması**
```bash
python flask_app.py
```

Tarayıcıda `http://localhost:5000` adresini açın.

### **Agent Seçimi**
Sidebar'da agent türünü seçin:
- 🔄 **RAG Agent**: Geleneksel yaklaşım
- ⚡ **SmolAgent**: Hızlı ve hafif
- 🔄 **LangGraph**: Gelişmiş workflow

## 🔧 API Endpoints

### **Chat API**
```http
POST /api/chat
Content-Type: application/json

{
    "message": "Batarya durumunu nasıl kontrol ederim?",
    "agent_type": "smol"
}
```

### **Agents API**
```http
GET /api/agents
```

Mevcut agent'ların durumunu döndürür.

## 🧪 Test

### **Manuel Test**
```python
from utils.agents.agent_factory import AgentFactory

factory = AgentFactory()

# SmolAgent test
smol_agent = factory.get_agent("smol")
response = smol_agent.chat("Batarya durumunu nasıl kontrol ederim?")
print(response)

# LangGraph test
langgraph_agent = factory.get_agent("langgraph")
response = langgraph_agent.chat("GPRS parametrelerini nasıl ayarlarım?")
print(response)
```

### **Otomatik Test**
```bash
python test_agents.py
```

## 🔄 Agent Geçişi

### **SmolAgent'dan LangGraph'a**

1. **Tool'ları Koru**: Tüm domain fonksiyonları `utils/tools.py`'de
2. **State Şeması**: LangGraph için `FM130State` TypedDict
3. **Workflow**: Node'lar ve edge'ler ile state machine
4. **Memory**: `MemorySaver` ile state persistence

### **Avantajlar**
- **Hızlı Başlangıç**: SmolAgent ile prototipleme
- **Gelişmiş Özellikler**: LangGraph ile complex workflow
- **Kod Paylaşımı**: Ortak tools ve helpers
- **Fallback**: Hata durumunda otomatik RAG

## 🚨 Sorun Giderme

### **SmolAgent Kurulum Hatası**
```bash
pip install smolagents
# veya
pip install git+https://github.com/smol-ai/smolagents.git
```

### **LangGraph Kurulum Hatası**
```bash
pip install langgraph
```

### **Tool Import Hatası**
```python
# utils/tools.py dosyasının doğru konumda olduğundan emin olun
from utils.tools import search_fm130_commands
```

### **Vector Store Hatası**
```python
# Vector index'in oluşturulduğundan emin olun
from vector.vector_store import VectorStore
store = VectorStore()
store.create_index(documents)
```

## 📊 Performans Karşılaştırması

| Agent Türü | Hız | Bellek | Özellik | Kullanım Alanı |
|------------|-----|--------|---------|----------------|
| **RAG** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Genel kullanım |
| **SmolAgent** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Hızlı prototipleme |
| **LangGraph** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Complex workflow |

## 🔮 Gelecek Geliştirmeler

1. **Multi-Agent Collaboration**: Agent'lar arası işbirliği
2. **Streaming Responses**: Real-time yanıtlar
3. **Custom Tools**: Kullanıcı tanımlı araçlar
4. **Agent Learning**: Kullanıcı etkileşimlerinden öğrenme
5. **Performance Metrics**: Agent performans ölçümleri

## 📞 Destek

Sorun yaşarsanız:
1. `python test_agents.py` çalıştırın
2. Console log'ları kontrol edin
3. Agent durumunu `/api/agents` endpoint'inden kontrol edin
4. Fallback agent otomatik olarak devreye girer

---

**Not**: Bu entegrasyon, mevcut RAG sistemini bozmadan yeni agent'ları ekler. Her agent aynı tools'ları kullanarak tutarlı yanıtlar verir. 