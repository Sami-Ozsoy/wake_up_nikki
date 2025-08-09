import re
from typing import Dict, Any

def format_llm_response(response: str) -> str:
    """
    LLM yanıtını basit şekilde formatlar
    """
    if not response:
        return "❌ Yanıt alınamadı."
    
    # Sadece temel temizlik
    formatted = response.strip()
    
    return formatted

def extract_sms_command(response: str) -> str:
    """
    Yanıttan SMS komutunu çıkarır
    """
    # Kod bloklarından SMS komutunu bul
    sms_pattern = r'```(?:sms)?\n?([^`]+)\n?```'
    match = re.search(sms_pattern, response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Backtick içindeki komutları bul
    backtick_pattern = r'`([^`]+)`'
    matches = re.findall(backtick_pattern, response)
    for match in matches:
        if any(keyword in match.lower() for keyword in ['sms', 'setparam', 'getparam', 'battery', 'reboot']):
            return match
    
    return ""

def create_structured_response(command_info: Dict[str, Any]) -> str:
    """
    Yapılandırılmış yanıt oluşturur
    """
    response_parts = []
    
    # Başlık
    response_parts.append("## 📋 Komut Bilgisi")
    
    # Komut bilgileri
    if command_info.get('name'):
        response_parts.append(f"### 🔍 **Komut Adı:** {command_info['name']}")
    
    if command_info.get('description'):
        response_parts.append(f"**Açıklama:** {command_info['description']}")
    
    # SMS formatı
    if command_info.get('sms_format'):
        response_parts.append("### 📱 **SMS Formatı**")
        response_parts.append(f"```\n{command_info['sms_format']}\n```")
    
    # Kullanım açıklaması
    if command_info.get('usage'):
        response_parts.append("### 💡 **Kullanım Açıklaması**")
        response_parts.append(command_info['usage'])
    
    # Parametre detayları
    if command_info.get('parameters'):
        response_parts.append("### ⚙️ **Parametre Detayları**")
        for param in command_info['parameters']:
            response_parts.append(f"- **{param['name']}:** {param['value']}")
    
    # Örnek kullanım
    if command_info.get('example'):
        response_parts.append("### 📝 **Örnek Kullanım**")
        response_parts.append(f"```\n{command_info['example']}\n```")
    
    return "\n\n".join(response_parts)

def format_error_response(error_msg: str) -> str:
    """
    Hata yanıtını formatlar
    """
    return f"""## ❌ **Hata Oluştu**

{error_msg}

### 💡 **Önerilen Çözümler:**
- Farklı bir soru sorun
- Aşağıdaki örnek sorulardan birini deneyin:
  - Batarya durumunu nasıl kontrol ederim?
  - GPRS parametrelerini nasıl ayarlarım?
  - Cihazı uzaktan nasıl yeniden başlatırım?"""

def format_no_info_response() -> str:
    """
    Bilgi bulunamadığında formatlar
    """
    return """## ❌ **Bilgi Bulunamadı**

Bu konuda bilgi bulunamadı. Lütfen farklı bir soru sorun veya aşağıdaki örnek sorulardan birini deneyin.

### 💡 **Önerilen Sorular:**
- Batarya durumunu nasıl kontrol ederim?
- GPRS parametrelerini nasıl ayarlarım?
- SMS/arama bildirimlerini nasıl yapılandırırım?
- Cihazı uzaktan nasıl yeniden başlatırım?
- Araç plakasını nasıl değiştiririm?""" 