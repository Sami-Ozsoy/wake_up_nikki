import streamlit as st
import time
import os

from config import OPENAI_API_KEY, NEO4J_URI
from utils.helpers import get_llm
from utils.loaders import load_prompt
from vector.vector_store import VectorStore
from utils.formatter import format_llm_response, format_error_response, format_no_info_response

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Niki - FM130 Komut Yardımcısı",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .chat-message {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .user-message {
        background: #e3f2fd;
        border-left-color: #2196f3;
    }
    .assistant-message {
        background: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .example-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        cursor: pointer;
    }
    .example-button:hover {
        background: linear-gradient(45deg, #5a6fd8, #6a4190);
    }
</style>
""", unsafe_allow_html=True)

# Başlık
st.markdown("""
<div class="main-header">
    <h1>🤖 Niki - FM130 Komut Yardımcısı</h1>
    <p>FM130 cihazı komutları konusunda size yardımcı olan akıllı asistan</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    # Model seçimi
    model_choice = st.selectbox(
        "Model Seçimi",
        ["gpt-3.5-turbo", "gpt-4"],
        index=0
    )
    
    # Sıcaklık ayarı
    temperature = st.slider("Yaratıcılık Seviyesi", 0.0, 1.0, 0.7, 0.1)
    
    st.divider()
    
    # Örnek sorular
    st.header("💡 Örnek Sorular")
    example_questions = [
        "Batarya durumunu nasıl kontrol ederim?",
        "GPRS parametrelerini nasıl ayarlarım?",
        "SMS/arama bildirimlerini nasıl yapılandırırım?",
        "Cihazı uzaktan nasıl yeniden başlatırım?",
        "GSM operatörlerini nasıl atarım?",
        "Araç plakasını nasıl değiştiririm?"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"example_{question}"):
            st.session_state.user_input = question

# Ana içerik
col1, col2 = st.columns([3, 1])

with col1:
    # Chat container
    chat_container = st.container()
    
    # Input alanı
    user_input = st.text_area(
        "Mesajınızı yazın...",
        key="user_input",
        height=100,
        placeholder="Örn: Batarya durumunu hangi komutla öğrenirim?"
    )
    
    # Gönder butonu
    col1_1, col1_2, col1_3 = st.columns([1, 1, 1])
    with col1_2:
        send_button = st.button("🚀 Gönder", use_container_width=True)

with col2:
    # İstatistikler
    st.header("📊 İstatistikler")
    if 'chat_count' not in st.session_state:
        st.session_state.chat_count = 0
    
    st.metric("Toplam Sohbet", st.session_state.chat_count)
    
    # Geçmişi temizle
    if st.button("🗑️ Geçmişi Temizle", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_count = 0

# Chat geçmişini başlat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj gönderme işlemi
if send_button and user_input:
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # LLM ve retriever ayarları
    try:
        llm = get_llm()
        vector_store = VectorStore()
        retriever = vector_store.get_retriever()
        
        # Prompt hazırla
        prompt_text = load_prompt("prompts/main_prompt.txt")
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        # Vector context ile input formatla
        retrieved_docs = retriever.get_relevant_documents(user_input)
        docs_content = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Chat geçmişini al
        chat_history = "\n".join([
            f"Kullanıcı: {msg['content']}\nAsistan: {msg.get('response', '')}" 
            for msg in st.session_state.messages[:-1]  # Son mesaj hariç
        ])
        
        full_context = f"{docs_content}\n\n{chat_history}\nKullanıcı: {user_input}"
        
        # Prompt'u formatla
        formatted_prompt = prompt.format(
            question=user_input,
            context=full_context
        )
        
        # LLM'den yanıt al
        with st.spinner("🤖 Niki düşünüyor..."):
            response = llm.invoke(formatted_prompt)
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Yanıtı formatla
            formatted_response = format_llm_response(response_content)
            
            # Eğer yanıt çok kısaysa veya hata içeriyorsa
            if len(formatted_response.strip()) < 50 or "bilgi bulunamadı" in formatted_response.lower():
                formatted_response = format_no_info_response()
        
        # Asistan yanıtını ekle
        st.session_state.messages.append({
            "role": "assistant", 
            "content": formatted_response,
            "response": formatted_response
        })
        
        # Sohbet sayısını artır
        st.session_state.chat_count += 1
        
        # Input'u temizle
        st.session_state.user_input = ""
        
    except Exception as e:
        error_response = format_error_response(str(e))
        st.session_state.messages.append({
            "role": "assistant", 
            "content": error_response,
            "response": error_response
        })

# Mesajları göster
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 Siz:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Niki:</strong><br>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(message["content"]) 