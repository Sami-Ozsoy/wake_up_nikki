# 🤖 Niki - FM130 Komut Yardımcısı

FM130 cihazı komutları konusunda size yardımcı olan RAG (Retrieval-Augmented Generation) tabanlı akıllı asistan.

## 📋 Özellikler

- **RAG Tabanlı Yanıtlar**: FM130 komut referanslarından akıllı bilgi çıkarımı
- **Çoklu Web Arayüzü**: Flask, Streamlit ve Gradio seçenekleri
- **ChatGPT Benzeri UI**: Modern ve kullanıcı dostu arayüz
- **Markdown Desteği**: Zengin formatlanmış yanıtlar
- **Örnek Sorular**: Hızlı başlangıç için önceden hazırlanmış sorular
- **Session Yönetimi**: Kullanıcı bazlı sohbet geçmişi

## 🏗️ Proje Yapısı

```
wake_up_nikki/
├── flask_app.py              # Flask uygulaması
├── main.py                   # Streamlit uygulaması
├── gradio_app.py             # Gradio uygulaması
├── config.py                 # Konfigürasyon ayarları
├── utils/                    # Yardımcı fonksiyonlar
│   ├── helpers.py           # LLM entegrasyonu
│   ├── loaders.py           # Prompt yükleme
│   └── formatter.py         # Yanıt formatlama
├── vector/                   # Vector store yönetimi
│   └── vector_store.py      # Vector store sınıfı
├── templates/                # HTML şablonları
│   └── chat.html           # Flask chat arayüzü
├── assets/                  # Statik dosyalar
│   └── niki.png           # Niki logosu
├── data/                    # Veri dosyaları
├── prompts/                 # Prompt şablonları
│   └── main_prompt.txt     # Ana prompt
├── vector/                  # Vector index dosyaları
├── requirements.txt         # Python bağımlılıkları
└── README.md               # Bu dosya
```

## 🚀 Kurulum

### 1. Gereksinimler

- Python 3.8+
- OpenAI API Key
- FM130 komut referans dosyaları

### 2. Kurulum Adımları

```bash
# Repository'yi klonlayın
git clone <repository-url>
cd wake_up_nikki

# Virtual environment oluşturun
python -m venv .venv

# Virtual environment'ı aktifleştirin
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Environment değişkenlerini ayarlayın
cp .env.example .env
# .env dosyasını düzenleyin ve OPENAI_API_KEY ekleyin
```

### 3. Veri Hazırlama

```bash
# FM130 komut referanslarını data/ klasörüne kopyalayın
# Örnek dosyalar:
# - FM130_Command_Reference.pdf
# - Directories.txt
# - FM130_Parameter_List.txt

# Vector index'i oluşturun
python -c "
from vector.vector_store import VectorStore
store = VectorStore()
docs = store.load_documents('data')
split_docs = store.split_documents(docs)
store.create_index(split_docs)
print('Vector index oluşturuldu!')
"
```

## 🎯 Kullanım

### Flask Uygulaması (Önerilen)

```bash
python flask_app.py
```

**Özellikler:**
- ChatGPT benzeri modern arayüz
- Real-time WebSocket desteği
- Markdown render desteği
- Kod kopyalama özelliği
- Responsive tasarım

### Streamlit Uygulaması

```bash
streamlit run main.py
```

**Özellikler:**
- Kolay kurulum ve kullanım
- Sidebar ile ayarlar
- Örnek soru butonları
- İstatistik paneli

### Gradio Uygulaması

```bash
python gradio_app.py
```

**Özellikler:**
- Hızlı prototipleme
- Otomatik API oluşturma
- Kolay paylaşım

## 🔧 Konfigürasyon

### Environment Değişkenleri

```bash
# .env dosyası
OPENAI_API_KEY=your_openai_api_key_here
NEO4J_URI=bolt://localhost:7687  # Opsiyonel
NEO4J_USERNAME=neo4j            # Opsiyonel
NEO4J_PASSWORD=password         # Opsiyonel
```

### Prompt Özelleştirme

`prompts/main_prompt.txt` dosyasını düzenleyerek AI asistanının davranışını özelleştirebilirsiniz.

## 📊 Arayüz Karşılaştırması

| Özellik | Flask | Streamlit | Gradio |
|---------|-------|-----------|--------|
| Kurulum Kolaylığı | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Özelleştirme | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Performans | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Modern UI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Deployment | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

## 💡 Örnek Kullanım

### Soru Örnekleri

1. **Batarya Durumu**
   ```
   "Batarya durumunu nasıl kontrol ederim?"
   ```

2. **GPRS Ayarları**
   ```
   "GPRS parametrelerini nasıl ayarlarım?"
   ```

3. **SMS Bildirimleri**
   ```
   "SMS/arama bildirimlerini nasıl yapılandırırım?"
   ```

4. **Uzaktan Kontrol**
   ```
   "Cihazı uzaktan nasıl yeniden başlatırım?"
   ```

### Yanıt Formatı

AI asistanı yanıtları şu formatta verir:

```markdown
## 📋 Komut Bilgisi

### 🔍 **Komut Adı:** [Komut adı]
**Açıklama:** [Komut açıklaması]

### 📱 **SMS Formatı**
```
[SMS komut formatı]
```

### 💡 **Kullanım Açıklaması**
[Türkçe açıklama]

### ⚙️ **Parametre Detayları**
- **Parametre ID:** [ID]
- **Parametre Tipi:** [Tip]
- **Varsayılan Değer:** [Değer]

### 📝 **Örnek Kullanım**
```
[Örnek SMS komutu]
```
```

## 🐳 Docker ile Çalıştırma

```bash
# Docker image oluşturun
docker build -t niki-fm130 .

# Container'ı çalıştırın
docker run -p 8501:8501 niki-fm130
```

## 🔍 Sorun Giderme

### Yaygın Hatalar

1. **"OPENAI_API_KEY not set"**
   - `.env` dosyasında API key'in doğru ayarlandığından emin olun

2. **"Vector index bulunamadı"**
   - `data/` klasöründe referans dosyalarının olduğunu kontrol edin
   - Vector index'i yeniden oluşturun

3. **Import hataları**
   - Virtual environment'ın aktif olduğundan emin olun
   - `pip install -r requirements.txt` komutunu çalıştırın

### Log Kontrolü

```bash
# Flask uygulaması için
python flask_app.py

# Streamlit uygulaması için
streamlit run main.py --server.port=8501
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

- **Proje Sahibi:** [Adınız]
- **Email:** [email@example.com]
- **Proje Linki:** [https://github.com/username/wake_up_nikki](https://github.com/username/wake_up_nikki)

---

**Not:** Bu proje FM130 cihazı komutları için eğitilmiş bir AI asistanıdır. Üretim ortamında kullanmadan önce gerekli testleri yapın. 