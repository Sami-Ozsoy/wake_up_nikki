import gradio as gr
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

# CSS stilleri
css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
}
.chat-container {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem;
    background: #f8f9fa;
}
.example-btn {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    margin: 0.25rem;
    cursor: pointer;
    transition: all 0.3s ease;
}
.example-btn:hover {
    background: linear-gradient(45deg, #5a6fd8, #6a4190);
    transform: translateY(-2px);
}
"""

# Header HTML
header_html = """
<div class="main-header">
    <h1>🤖 Niki - FM130 Komut Yardımcısı</h1>
    <p>FM130 cihazı komutları konusunda size yardımcı olan akıllı asistan</p>
</div>
"""

# Chat geçmişi
chat_history = []

def get_response(message, history):
    """Kullanıcı mesajına yanıt ver"""
    try:
        # LLM ve retriever ayarları
        llm = get_llm()
        vector_store = VectorStore()
        retriever = vector_store.get_retriever()
        
        # Prompt hazırla
        prompt_text = load_prompt("prompts/main_prompt.txt")
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        # Vector context ile input formatla
        retrieved_docs = retriever.get_relevant_documents(message)
        docs_content = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Chat geçmişini al
        chat_context = "\n".join([f"Kullanıcı: {q}\nAsistan: {a}" for q, a in history])
        
        full_context = f"{docs_content}\n\n{chat_context}\nKullanıcı: {message}"
        
        # Prompt'u formatla
        formatted_prompt = prompt.format(
            question=message,
            context=full_context
        )
        
        # LLM'den yanıt al
        response = llm.invoke(formatted_prompt)
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Yanıtı formatla
        formatted_response = format_llm_response(response_content)
        
        # Eğer yanıt çok kısaysa veya hata içeriyorsa
        if len(formatted_response.strip()) < 50 or "bilgi bulunamadı" in formatted_response.lower():
            formatted_response = format_no_info_response()
        
        return formatted_response
        
    except Exception as e:
        return format_error_response(str(e))

def clear_chat():
    """Chat geçmişini temizle"""
    global chat_history
    chat_history = []
    return [], ""

def set_example(example_text):
    """Örnek soruyu input'a yerleştir"""
    return example_text

# Gradio arayüzü
with gr.Blocks(css=css, title="Niki - FM130 Komut Yardımcısı") as demo:
    gr.HTML(header_html)
    
    with gr.Row():
        with gr.Column(scale=3):
            # Chatbot
            chatbot = gr.Chatbot(
                label="💬 Sohbet", 
                height=500, 
                show_label=True, 
                container=True, 
                bubble_full_width=False
            )
            
            # Input alanı
            with gr.Row():
                msg = gr.Textbox(
                    label="Mesajınızı yazın...", 
                    placeholder="Örn: Batarya durumunu hangi komutla öğrenirim?", 
                    scale=4
                )
                send_btn = gr.Button("🚀 Gönder", scale=1)
            
            # Kontrol butonları
            with gr.Row():
                clear_btn = gr.Button("🗑️ Geçmişi Temizle", scale=1)
                gr.HTML(f"<div style='text-align: right; color: #666;'>Toplam Sohbet: {len(chat_history)}</div>", scale=2)
        
        with gr.Column(scale=1):
            # Hızlı erişim
            gr.Markdown("### 🛠️ Hızlı Erişim")
            
            # Örnek sorular
            gr.Markdown("### 💡 Örnek Sorular")
            
            example_questions = [
                "Batarya durumunu nasıl kontrol ederim?",
                "GPRS parametrelerini nasıl ayarlarım?",
                "SMS/arama bildirimlerini nasıl yapılandırırım?",
                "Cihazı uzaktan nasıl yeniden başlatırım?",
                "GSM operatörlerini nasıl atarım?",
                "Araç plakasını nasıl değiştiririm?"
            ]
            
            for question in example_questions:
                example_btn = gr.Button(
                    question, 
                    variant="secondary", 
                    size="sm",
                    elem_classes=["example-btn"]
                )
                example_btn.click(
                    fn=set_example,
                    inputs=[],
                    outputs=msg,
                    _js=f"() => '{question}'"
                )
    
    # Event handlers
    def user_input_handler(message, history):
        if not message.strip():
            return history, ""
        
        response = get_response(message, history)
        history.append((message, response))
        return history, ""
    
    # Event bağlantıları
    send_btn.click(
        fn=user_input_handler,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )
    
    msg.submit(
        fn=user_input_handler,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )
    
    clear_btn.click(
        fn=clear_chat,
        inputs=[],
        outputs=[chatbot, msg]
    )

# Uygulamayı başlat
if __name__ == "__main__":
    print("🚀 Gradio uygulaması başlatılıyor...")
    print("📱 Tarayıcıda gösterilen adresi açın")
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860) 