from typing import List, Dict, Any
from vector.vector_store import VectorStore
import re

# Vector store instance
_vector_store = VectorStore()

def search_fm130_commands(query: str) -> List[Dict[str, Any]]:
    """
    FM130 komutlarını vector store'da ara
    
    Args:
        query: Arama sorgusu
        
    Returns:
        List[Dict]: Bulunan komutlar ve metadata'ları
    """
    try:
        # Vector search yap
        docs_with_scores = _vector_store.similarity_search_with_score(query, k=5)
        
        # Sonuçları formatla
        results = []
        for doc, score in docs_with_scores:
            if score > 0.6:  # Sadece yüksek kaliteli sonuçları al
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score,
                    'source': doc.metadata.get('source', 'Unknown')
                })
        
        return results
    except Exception as e:
        print(f"Komut arama hatası: {e}")
        return []

def get_command_details(command_name: str) -> Dict[str, Any]:
    """
    Belirli bir komutun detaylarını getir
    
    Args:
        command_name: Komut adı
        
    Returns:
        Dict: Komut detayları
    """
    try:
        # Komut adına göre arama yap
        results = search_fm130_commands(command_name)
        
        if results:
            # En iyi eşleşmeyi al
            best_match = results[0]
            
            # Komut bilgilerini parse et
            content = best_match['content']
            
            # SMS komut formatını bul
            sms_pattern = r'```(?:sms)?\n?([^`]+)\n?```'
            sms_match = re.search(sms_pattern, content, re.IGNORECASE)
            sms_format = sms_match.group(1).strip() if sms_match else ""
            
            return {
                'name': command_name,
                'description': content[:200] + "..." if len(content) > 200 else content,
                'sms_format': sms_format,
                'source': best_match['source'],
                'score': best_match['score']
            }
        else:
            return {
                'name': command_name,
                'description': 'Komut bulunamadı',
                'sms_format': '',
                'source': 'Unknown',
                'score': 0.0
            }
    except Exception as e:
        print(f"Komut detay hatası: {e}")
        return {
            'name': command_name,
            'description': f'Hata: {str(e)}',
            'sms_format': '',
            'source': 'Error',
            'score': 0.0
        }

def validate_parameters(command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    FM130 parametrelerini doğrula
    
    Args:
        command: Komut adı
        parameters: Doğrulanacak parametreler
        
    Returns:
        Dict: Doğrulama sonucu
    """
    try:
        # Komut detaylarını al
        command_info = get_command_details(command)
        
        if not command_info or command_info['description'] == 'Komut bulunamadı':
            return {
                'valid': False,
                'errors': ['Komut bulunamadı'],
                'suggestions': []
            }
        
        # Basit parametre doğrulama (gerçek projede daha gelişmiş olabilir)
        validation_result = {
            'valid': True,
            'errors': [],
            'suggestions': [],
            'command_info': command_info
        }
        
        # Parametre sayısı kontrolü
        if len(parameters) == 0:
            validation_result['suggestions'].append('Parametre gerekli olabilir')
        
        return validation_result
        
    except Exception as e:
        return {
            'valid': False,
            'errors': [f'Doğrulama hatası: {str(e)}'],
            'suggestions': []
        }

def create_configuration_plan(requirements: str) -> Dict[str, Any]:
    """
    FM130 konfigürasyon planı oluştur
    
    Args:
        requirements: Kullanıcı gereksinimleri
        
    Returns:
        Dict: Konfigürasyon planı
    """
    try:
        # Gereksinimlere göre ilgili komutları ara
        relevant_commands = search_fm130_commands(requirements)
        
        if not relevant_commands:
            return {
                'plan': 'Gereksinimlere uygun komut bulunamadı',
                'commands': [],
                'steps': []
            }
        
        # Plan oluştur
        plan = {
            'requirements': requirements,
            'commands': relevant_commands[:3],  # En iyi 3 komutu al
            'steps': [
                '1. Gerekli komutları belirle',
                '2. Parametreleri ayarla', 
                '3. Test et',
                '4. Doğrula'
            ],
            'estimated_time': '5-10 dakika'
        }
        
        return plan
        
    except Exception as e:
        return {
            'plan': f'Plan oluşturma hatası: {str(e)}',
            'commands': [],
            'steps': []
        }

def troubleshoot_fm130_issue(issue_description: str) -> Dict[str, Any]:
    """
    FM130 sorunlarını teşhis et ve çözüm öner
    
    Args:
        issue_description: Sorun açıklaması
        
    Returns:
        Dict: Sorun teşhisi ve çözüm önerileri
    """
    try:
        # Sorun açıklamasına göre ilgili komutları ara
        relevant_commands = search_fm130_commands(issue_description)
        
        # Sorun türünü belirle
        issue_type = 'unknown'
        if any(word in issue_description.lower() for word in ['batarya', 'battery', 'power']):
            issue_type = 'battery'
        elif any(word in issue_description.lower() for word in ['gprs', 'internet', 'bağlantı']):
            issue_type = 'connectivity'
        elif any(word in issue_description.lower() for word in ['sms', 'mesaj']):
            issue_type = 'communication'
        
        # Çözüm önerileri
        solutions = {
            'battery': [
                'Batarya durumunu kontrol et: GETPARAM 1',
                'Şarj cihazını kontrol et',
                'Batarya değişimi gerekebilir'
            ],
            'connectivity': [
                'GPRS ayarlarını kontrol et: GETPARAM 10',
                'SIM kart durumunu kontrol et',
                'Operatör ayarlarını doğrula'
            ],
            'communication': [
                'SMS ayarlarını kontrol et: GETPARAM 5',
                'Telefon numarasını doğrula',
                'Sinyal gücünü kontrol et'
            ],
            'unknown': [
                'Cihazı yeniden başlat: REBOOT',
                'Parametreleri sıfırla: RESET',
                'Teknik destek ile iletişime geç'
            ]
        }
        
        return {
            'issue_type': issue_type,
            'description': issue_description,
            'relevant_commands': relevant_commands[:2],
            'solutions': solutions.get(issue_type, solutions['unknown']),
            'diagnostic_steps': [
                '1. Cihaz durumunu kontrol et',
                '2. Hata kodlarını not al',
                '3. Önerilen çözümleri dene',
                '4. Gerekirse teknik destek al'
            ]
        }
        
    except Exception as e:
        return {
            'issue_type': 'error',
            'description': issue_description,
            'error': str(e),
            'solutions': ['Teknik destek ile iletişime geç'],
            'diagnostic_steps': []
        } 