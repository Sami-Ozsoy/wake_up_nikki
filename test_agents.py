#!/usr/bin/env python3
"""
FM130 Agent Test Script
Bu script tüm agent'ların düzgün çalışıp çalışmadığını test eder.
"""

import os
import sys
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

# Proje kök dizinini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tools():
    """Tools fonksiyonlarını test et"""
    print("🔧 Tools test ediliyor...")
    
    try:
        from utils.tools import search_fm130_commands, get_command_details
        
        # Test sorgusu
        test_query = "batarya"
        print(f"Test sorgusu: '{test_query}'")
        
        # Komut arama testi
        results = search_fm130_commands(test_query)
        print(f"Bulunan komutlar: {len(results)}")
        
        if results:
            print(f"İlk sonuç: {results[0]['content'][:100]}...")
        
        # Komut detay testi
        if results:
            command_name = "GETPARAM"
            details = get_command_details(command_name)
            print(f"Komut detayları: {details['name']}")
        
        print("✅ Tools test başarılı!\n")
        return True
        
    except Exception as e:
        print(f"❌ Tools test hatası: {e}")
        return False

def test_smol_agent():
    """SmolAgent'ı test et"""
    print("⚡ SmolAgent test ediliyor...")
    
    try:
        from utils.agents.smol_agent import FM130SmolAgent
        
        agent = FM130SmolAgent()
        print(f"Agent oluşturuldu: {agent.get_agent_info()['name']}")
        
        # Test mesajı
        test_message = "Batarya durumunu nasıl kontrol ederim?"
        print(f"Test mesajı: '{test_message}'")
        
        response = agent.chat(test_message)
        print(f"Yanıt alındı: {len(response)} karakter")
        print(f"Yanıt önizleme: {response[:100]}...")
        
        print("✅ SmolAgent test başarılı!\n")
        return True
        
    except Exception as e:
        print(f"❌ SmolAgent test hatası: {e}")
        return False

def test_langgraph_agent():
    """LangGraph agent'ı test et"""
    print("🔄 LangGraph Agent test ediliyor...")
    
    try:
        from utils.agents.langgraph_agent import FM130LangGraphAgent
        
        agent = FM130LangGraphAgent()
        print(f"Agent oluşturuldu: {agent.get_agent_info()['name']}")
        
        # Test mesajı
        test_message = "GPRS parametrelerini nasıl ayarlarım?"
        print(f"Test mesajı: '{test_message}'")
        
        response = agent.chat(test_message)
        print(f"Yanıt alındı: {len(response)} karakter")
        print(f"Yanıt önizleme: {response[:100]}...")
        
        print("✅ LangGraph Agent test başarılı!\n")
        return True
        
    except Exception as e:
        print(f"❌ LangGraph Agent test hatası: {e}")
        return False

def test_agent_factory():
    """Agent factory'yi test et"""
    print("🏭 Agent Factory test ediliyor...")
    
    try:
        from utils.agents.agent_factory import AgentFactory
        
        factory = AgentFactory()
        
        # Mevcut agent'ları listele
        available_agents = factory.get_available_agents()
        print(f"Mevcut agent'lar: {len(available_agents)}")
        
        for agent_type, agent_info in available_agents.items():
            status = "✅" if agent_info['status'] == 'available' else "❌"
            print(f"  {status} {agent_type}: {agent_info['name']}")
        
        # RAG agent testi
        rag_agent = factory.get_agent("rag")
        print(f"RAG agent oluşturuldu: {rag_agent.get_agent_info()['name']}")
        
        # Test mesajı
        test_message = "SMS bildirimlerini nasıl yapılandırırım?"
        response = rag_agent.chat(test_message)
        print(f"RAG yanıtı: {len(response)} karakter")
        
        print("✅ Agent Factory test başarılı!\n")
        return True
        
    except Exception as e:
        print(f"❌ Agent Factory test hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 FM130 Agent Test Script Başlatılıyor...\n")
    
    tests = [
        test_tools,
        test_smol_agent,
        test_langgraph_agent,
        test_agent_factory
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test çalıştırma hatası: {e}")
            results.append(False)
    
    # Sonuçları özetle
    print("📊 Test Sonuçları:")
    print("=" * 50)
    
    test_names = ["Tools", "SmolAgent", "LangGraph", "Agent Factory"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{name:15}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print("=" * 50)
    print(f"Toplam: {success_count}/{total_count} test başarılı")
    
    if success_count == total_count:
        print("🎉 Tüm testler başarılı! Agent'lar hazır.")
    else:
        print("⚠️  Bazı testler başarısız. Lütfen hataları kontrol edin.")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 