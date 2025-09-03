import os
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import time

from utils.helpers import get_llm
from utils.loaders import load_prompt
from vector.vector_store import VectorStore
from utils.formatter import format_llm_response, format_error_response, format_no_info_response

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain.memory import ConversationBufferMemory
from agents.graph import invoke_graph
 

# Proje kök dizinini bul
project_root = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
           static_folder=os.path.join(project_root, 'assets'), 
           static_url_path='/static',
           template_folder=os.path.join(project_root, 'templates'))
app.config['SECRET_KEY'] = 'niki-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Bellek (session bazlı)
session_memories = {}

# Prompt hazırla
prompt_text = load_prompt("prompts/main_prompt.txt")
prompt = ChatPromptTemplate.from_template(prompt_text)

# LLM ve retriever ayarları
llm = get_llm()
vector_store = VectorStore()

def get_memory(session_id: str) -> ConversationBufferMemory:
    """Session'a bağlı bellek nesnesini döndür (yoksa oluştur)."""
    mem = session_memories.get(session_id)
    if mem is None:
        mem = ConversationBufferMemory(memory_key="history", input_key="question", return_messages=True)
        session_memories[session_id] = mem
    return mem

def format_input_with_vector_context(user_input, session_id):
    """Vector context ile input formatla"""
    try:
        # Her seferinde yeni bir retriever oluştur
        retriever = vector_store.get_retriever(k=6)  # Optimal sayı
        retrieved_docs = retriever.invoke(user_input)
        
        # Debug: Hangi dokümanların alındığını göster
        print(f"----->Retrieved {len(retrieved_docs)} documents for: '{user_input}'")
        
        # Score'larla birlikte similarity search yap
        docs_with_scores = vector_store.similarity_search_with_score(user_input, k=6)
        
        # Sadece yüksek score'lu dokümanları al (0.7+)
        high_quality_docs = []
        for doc, score in docs_with_scores:
            print(f"----->Doc Score: {score:.3f} - {doc.page_content[:100]}...")
            if score > 0.7:  # Sadece yüksek kaliteli dokümanları al
                high_quality_docs.append(doc)
        
        if not high_quality_docs:
            print("----->No high-quality documents found, using all retrieved docs")
            high_quality_docs = retrieved_docs
        
        docs_content = "\n\n".join([doc.page_content for doc in high_quality_docs])

        mem = get_memory(session_id)
        # Bellekten sohbet geçmişini oku
        messages = getattr(mem, "chat_memory").messages if hasattr(mem, "chat_memory") else []
        formatted_pairs = []
        for m in messages:
            # LangChain mesaj tiplerini basit metne çevir
            cls = m.__class__.__name__.lower()
            if hasattr(m, 'content'):
                if 'human' in cls:
                    formatted_pairs.append(f"Kullanıcı: {m.content}")
                elif 'ai' in cls:
                    formatted_pairs.append(f"Asistan: {m.content}")
        chat_context = "\n".join(formatted_pairs)

        full_context = f"{docs_content}\n\n{chat_context}\nKullanıcı: {user_input}"
        return {
            "question": user_input,
            "context": full_context
        }
    except Exception as e:
        print(f"Vector context hatası: {e}")
        return {
            "question": user_input,
            "context": f"Kullanıcı: {user_input}"
        }

def format_chat_history(input_data):
    """Chat history ve vector context'i formatla"""
    user_input = input_data["user_input"]
    session_id = input_data["session_id"]
    
    try:
        # Her seferinde yeni bir retriever oluştur
        retriever = vector_store.get_retriever(k=6)
        # Vector context al
        retrieved_docs = retriever.invoke(user_input)
        
        # Debug: Hangi dokümanların alındığını göster
        print(f"----->Chain Retrieved {len(retrieved_docs)} documents for: '{user_input}'")
        
        # Score'larla birlikte similarity search yap
        docs_with_scores = vector_store.similarity_search_with_score(user_input, k=6)
        
        # Sadece yüksek score'lu dokümanları al
        high_quality_docs = []
        for doc, score in docs_with_scores:
            print(f"----->Chain Doc Score: {score:.3f} - {doc.page_content[:100]}...")
            if score > 0.7:
                high_quality_docs.append(doc)
        
        if not high_quality_docs:
            high_quality_docs = retrieved_docs
            
        docs_content = "\n\n".join([doc.page_content for doc in high_quality_docs])

        # Chat history al (ConversationBufferMemory)
        mem = get_memory(session_id)
        messages = getattr(mem, "chat_memory").messages if hasattr(mem, "chat_memory") else []
        formatted_pairs = []
        for m in messages:
            cls = m.__class__.__name__.lower()
            if hasattr(m, 'content'):
                if 'human' in cls:
                    formatted_pairs.append(f"Kullanıcı: {m.content}")
                elif 'ai' in cls:
                    formatted_pairs.append(f"Asistan: {m.content}")
        chat_context = "\n".join(formatted_pairs)

        # Tam context oluştur
        full_context = f"{docs_content}\n\n{chat_context}\nKullanıcı: {user_input}"
        
        return {
            "question": user_input,
            "context": full_context
        }
    except Exception as e:
        print(f"Vector context hatası: {e}")
        return {
            "question": user_input,
            "context": f"Kullanıcı: {user_input}"
        }
    
chain = (
    RunnableLambda(format_chat_history)
    | prompt
    | llm
    | StrOutputParser()
)

def get_response(user_input, session_id):
    """Kullanıcı mesajına yanıt ver"""
    try:
        USE_GRAPH = True
        if USE_GRAPH:
            # Geçmişi hazırla
            mem = get_memory(session_id)
            messages = getattr(mem, "chat_memory").messages if hasattr(mem, "chat_memory") else []
            formatted_pairs = []
            for m in messages:
                cls = m.__class__.__name__.lower()
                if hasattr(m, 'content'):
                    if 'human' in cls:
                        formatted_pairs.append(f"Kullanıcı: {m.content}")
                    elif 'ai' in cls:
                        formatted_pairs.append(f"Asistan: {m.content}")
            history_text = "\n".join(formatted_pairs)

            ai_answer = invoke_graph(user_input, history_text=history_text)

            # Belleğe yazmayı sürdür
            try:
                mem.save_context({"question": user_input}, {"answer": ai_answer})
            except Exception as e:
                print(f"Bellek hatası: {e}")
                pass

            return format_llm_response(ai_answer)

        # ... (mevcut fallback zinciri olduğu gibi kalsın)

        context_data = format_input_with_vector_context(user_input, session_id)
        print(f"----->Context data length: {len(context_data['context'])}")
        formatted_prompt = prompt.format(**context_data)
        response = llm.invoke(formatted_prompt)
        response_content = response.content if hasattr(response, 'content') else str(response)
        formatted_response = format_llm_response(response_content)
        if len(formatted_response.strip()) < 50 or "bilgi bulunamadı" in formatted_response.lower():
            return format_no_info_response()

        mem = get_memory(session_id)
        try:
            mem.save_context({"question": user_input}, {"answer": formatted_response})
        except Exception:
            pass

        return formatted_response
    except Exception as e:
        print(f"Yanıt alma hatası: {e}")
        return format_error_response(str(e))

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    client_session_id = data.get('session_id')

    # İstek ile session_id geldiyse session'a yaz
    if client_session_id:
        session['session_id'] = client_session_id

    # Session'da yoksa bir kez üret ve kaydet
    if 'session_id' not in session:
        session['session_id'] = str(time.time())

    session_id = session['session_id']

    # Bellek hazırla
    _ = get_memory(session_id)

    if not message:
        return jsonify({'error': 'Boş mesaj gönderilemez'})

    try:
        print(f"----->Kullanıcı mesajı: {message}")
        print(f"----->Session ID: {session_id}")
        response = get_response(message, session_id)

        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': f'Hata oluştu: {str(e)}'})

@app.route('/api/clear', methods=['POST'])
def clear_history():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': True})
    session_memories[session_id] = ConversationBufferMemory(memory_key="history", input_key="question", return_messages=True)
    return jsonify({'success': True})

@app.route('/api/examples', methods=['GET'])
def get_examples():
    examples = [
        "Batarya durumunu nasıl kontrol ederim?",
        "GPRS parametrelerini nasıl ayarlarım?",
        "SMS/arama bildirimlerini nasıl yapılandırırım?",
        "Cihazı uzaktan nasıl yeniden başlatırım?",
        "Araç plakasını nasıl değiştiririm?"
    ]
    return jsonify({'examples': examples})

@socketio.on('connect')
def handle_connect():
    session_id = str(time.time())
    session['session_id'] = session_id
    emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    session_id = session.get('session_id')
    if session_id and session_id in session_memories:
        del session_memories[session_id]

if __name__ == '__main__':
    print("�� Flask uygulaması başlatılıyor...")
    print("📱 Tarayıcıda http://localhost:5000 adresini açın")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
