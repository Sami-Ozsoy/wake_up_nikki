import re
from typing import Dict, Any

def format_llm_response(response: str) -> str:
    """
    LLM yanıtını basit şekilde formatlar
    """
    return response.strip() if response else "❌ Yanıt alınamadı."

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
    """Yapılandırılmış yanıt oluşturur."""
    parts = ["## 📋 Komut Bilgisi"]
    name = command_info.get('name')
    if name:
        parts.append(f"### 🔍 **Komut Adı:** {name}")
    desc = command_info.get('description')
    if desc:
        parts.append(f"**Açıklama:** {desc}")
    sms = command_info.get('sms_format')
    if sms:
        parts.append("### 📱 **SMS Formatı**")
        parts.append(f"```\n{sms}\n```")
    usage = command_info.get('usage')
    if usage:
        parts.append("### 💡 **Kullanım Açıklaması**")
        parts.append(usage)
    params = command_info.get('parameters') or []
    if params:
        parts.append("### ⚙️ **Parametre Detayları**")
        parts.extend([f"- **{p.get('name')}:** {p.get('value')}" for p in params])
    example = command_info.get('example')
    if example:
        parts.append("### 📝 **Örnek Kullanım**")
        parts.append(f"```\n{example}\n```")
    return "\n\n".join(parts)

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