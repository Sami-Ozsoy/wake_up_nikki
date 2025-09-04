from typing import TypedDict, Literal, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
import requests
from bs4 import BeautifulSoup
from utils.loaders import load_prompt

# config.py'ye ekle
GOOGLE_SEARCH_API_KEY = "AIzaSyB60NcVpZgK-2yPGmhuB66CX8pWo28zE8c"
GOOGLE_SEARCH_ENGINE_ID = "47cb3390ff9684628"


MAIN_PROMPT = load_prompt("prompts/main_prompt.txt")

# Basit LLM tabanlı niyet sınıflandırıcı promptu
_INTENT_SYSTEM = (
    "You are a classifier. Decide if the user's request is about Teltonika FMB devices, "
    "commands or parameters (including FMB120/FMB130/FM130). "
    "Check the dialogue in the conversation and determine whether the user's question is a general conversation or one about the FMB 130 device, depending on its subject. Remember, the user can ask multiple and consecutive questions about the FMB 130. "
    "Return EXACTLY one word with no punctuation: fmb130 or general."
)

@tool("search_fmb_docs")
def search_fmb_docs(query: str, k: int = 6) -> List[str]:
    """
    This tool returns relevant passages from FMB documents.

    """
    print(f"🔍 [RAG SEARCH] Gelen query: '{query}', k={k}")
    
    from vector.vector_store import VectorStore
    vs = VectorStore(index_path="vector/index")
    results = vs.similarity_search_with_score(query, k=k)
    
    print(f"🔍 [RAG SEARCH] Toplam {len(results)} sonuç bulundu")
    for i, (doc, score) in enumerate(results):
        print(f"🔍 [RAG SEARCH] Sonuç {i+1}: Score={score:.3f}, İçerik={doc.page_content[:100]}...")
    
    high_quality = [doc for (doc, score) in results if score > 0.7]
    if not high_quality:
        high_quality = [doc for (doc, _) in results]
        print(f"🔍 [RAG SEARCH] Yüksek kalite sonuç yok, tüm sonuçlar kullanılıyor")
    else:
        print(f"🔍 [RAG SEARCH] {len(high_quality)} yüksek kalite sonuç seçildi")
    
    final_docs = [doc.page_content for doc in high_quality]
    print(f"🔍 [RAG SEARCH] Dönen doküman sayısı: {len(final_docs)}")
    return final_docs

@tool("optimize_search_query")
def optimize_search_query(user_query: str, history_text: str) -> str:
    """
    This tool generates an optimized search query in English by analyzing the user question and dialogue history.
    """
    print(f"🔍 [QUERY OPTIMIZER] Gelen query: '{user_query}'")
    print(f"🔍 [QUERY OPTIMIZER] Geçmiş uzunluğu: {len(history_text)} karakter")
    
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    
    optimization_prompt = f"""
        You're a search query optimization expert. By analyzing the user's question and conversation history,

        generate the most effective web search query about the Teltonika FMB130 device.

        Rules:

        1. Use short, concise search terms of only 3-5 words.

        2. Include technical terms and parameter names.

        3. Translate Turkish terms into English.

        4. Remove unnecessary words.
    
    Dialog History:
    {history_text}
    
    User Question:
    {user_query}
    
    Optimized search query (only return search terms, no explanation):
    """
    
    optimized_query = llm.invoke(optimization_prompt).content.strip()
    print(f"🔍 [QUERY OPTIMIZER] Optimize edilmiş sorgu: '{optimized_query}'")
    
    return optimized_query

@tool("web_search")
def web_search(query: str, max_results: int = 3) -> List[str]:
    """
    This tool searches only Teltonika sites for FMB130 content.
    """
    print(f"🌐 [WEB SEARCH] Gelen query: '{query}', max_results={max_results}")
    
    try:
        # Sadece Teltonika alan adları ve FMB130 içerikleri
        TELTONIKA_DOMAINS = [
            "teltonika-gps.com",
            "wiki.teltonika-gps.com",
            "teltonika.lt",
            "teltonika.org",
        ]
        site_filter = " OR ".join([f"site:{d}" for d in TELTONIKA_DOMAINS])

        # FMB130 vurgulu, Teltonika ile kısıtlı sorgu
        base_terms = f"FMB130 {query}".strip()
        search_query = f"({base_terms}) ({site_filter})"
        print(f"🌐 [WEB SEARCH] Arama sorgusu: '{search_query}'")
        
        def allow_url(url_or_text: str) -> bool:
            s = (url_or_text or "").lower()
            domain_ok = any(d in s for d in TELTONIKA_DOMAINS)
            fmb_ok = "fmb130" in s
            return domain_ok and fmb_ok

        # 1) DuckDuckGo Instant Answer API (+ site: filtreli)
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(search_query)}&format=json&no_html=1&skip_disambig=1"
        print(f"🌐 [WEB SEARCH] API URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"🌐 [WEB SEARCH] HTTP Status: {response.status_code}")
        
        results: List[str] = []
        if response.status_code == 200:
            data = response.json()
            print(f"🌐 [WEB SEARCH] API Response keys: {list(data.keys())}")
            
            # Abstract (özet bilgi) — kaynak alan adı ve fmb130 filtresi
            abstract = (data.get('Abstract') or '').strip()
            abstract_url = (data.get('AbstractURL') or '').strip()
            if abstract and abstract_url and allow_url(abstract_url):
                results.append(f"Özet: {abstract}\n{abstract_url}")
                print(f"🌐 [WEB SEARCH] Abstract eklendi")

            # Related topics
            related_topics = data.get('RelatedTopics', []) or []
            print(f"🌐 [WEB SEARCH] {len(related_topics)} related topic bulundu")
            for topic in related_topics:
                if isinstance(topic, dict):
                    text = (topic.get('Text') or '').strip()
                    first_url = ''
                    if 'FirstURL' in topic:
                        first_url = (topic.get('FirstURL') or '').strip()
                    elif 'Topics' in topic and topic['Topics']:
                        first_url = (topic['Topics'][0].get('FirstURL') or '').strip()
                        text = (topic['Topics'][0].get('Text') or text).strip()
                    if (text or first_url) and (allow_url(first_url) or allow_url(text)):
                        formatted = (f"{text} - {first_url}".strip() if first_url else text)
                        results.append(formatted)

        # 2) Google Custom Search API (sorguya site: filtresi gömülü)
        if len(results) < max_results:
            print("🌐 [WEB SEARCH] DDG kısıtlı, Google CSE deneniyor...")
            try:
                from agents.graph import GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_ENGINE_ID
                if GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
                    g_q = search_query  # site: filtreli
                    g_url = (
                        "https://www.googleapis.com/customsearch/v1"
                        f"?q={requests.utils.quote(g_q)}"
                        f"&key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}"
                    )
                    g_resp = requests.get(g_url,  timeout=10)
                    print(f"🌐 [WEB SEARCH] Google CSE HTTP Status: {g_resp.status_code}")
                    if g_resp.status_code == 200:
                        g_data = g_resp.json()
                        items = g_data.get('items', []) or []
                        for item in items:
                            title = (item.get('title') or '').strip()
                            link = (item.get('link') or '').strip()
                            snippet = (item.get('snippet') or '').strip()
                            if (title or snippet) and allow_url(link) and len(results) < max_results:
                                formatted = f"{title} - {link}\n{snippet}".strip()
                                results.append(formatted)
                                print(f"🌐 [WEB SEARCH] Google CSE sonuç eklendi: {link}")
            except Exception as ge:
                print(f"🌐 [WEB SEARCH] Google CSE fallback hatası: {ge}")
        
        # 3) DuckDuckGo HTML scrape (site: filtreli; sadece Teltonika + fmb130 linkleri)
        if len(results) < max_results:
            print("🌐 [WEB SEARCH] CSE de sınırlı, DDG HTML scrape deneniyor...")
            try:
                html_url = f"https://duckduckgo.com/html/?q={requests.utils.quote(search_query)}"
                html_resp = requests.get(html_url, timeout=10)
                if html_resp.status_code == 200:
                    soup = BeautifulSoup(html_resp.text, 'html.parser')
                    blocks = soup.select('.result')
                    for b in blocks:
                        a = b.select_one('.result__a')
                        snippet_el = b.select_one('.result__snippet')
                        if not a: 
                            continue
                        title = a.get_text(strip=True)
                        href = a.get('href', '')
                        if not allow_url(href) and not allow_url(title):
                            continue
                        snip = snippet_el.get_text(strip=True) if snippet_el else ''
                        formatted = f"{title} - {href}\n{snip}".strip()
                        if formatted:
                            results.append(formatted)
                            if len(results) >= max_results:
                                break
                print(f"🌐 [WEB SEARCH] DDG HTML scrape sonrası sonuç sayısı: {len(results)}")
            except Exception as se:
                print(f"🌐 [WEB SEARCH] DDG HTML scrape hatası: {se}")
        
        print(f"🌐 [WEB SEARCH] Sonuçlar: {results}")
        # 4) Son olarak hiçbir sonuç yoksa boş dön (genel arama YAPMA)
        final_results = results[:max_results] if results else []
        print(f"🌐 [WEB SEARCH] Dönen sonuç sayısı: {len(final_results)}")
        return final_results
    
    except Exception as e:
        print(f"🌐 [WEB SEARCH] Hata: {e}")
        return []

class GraphState(TypedDict):
    messages: List[dict]
    intent: Optional[Literal["fmb", "general", "unknown"]]
    context_docs: Optional[List[str]]
    web_results: Optional[List[str]]
    history_text: Optional[str]

def classify_intent(user_msg: str, history_text: str) -> Literal["fmb", "general"]:
    print(f"🎯 [INTENT CLASSIFIER] Gelen mesaj: '{user_msg}'")
    print(f"🎯 [INTENT CLASSIFIER] Geçmiş metin uzunluğu: {len(history_text)} karakter")
    
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    prompt = (
        f"{_INTENT_SYSTEM}\n\n"
        f"History:\n{history_text}\n\n"
        f"User:\n{user_msg}\n\n"
        "Answer:"
    )
    
    print(f"🎯 [INTENT CLASSIFIER] LLM'e gönderilen prompt uzunluğu: {len(prompt)} karakter")
    
    label = llm.invoke(prompt).content.strip().lower()
    print(f"🎯 [INTENT CLASSIFIER] LLM yanıtı: '{label}'")
    
    intent = "fmb" if "fmb" in label or "teltonika" in label else "general"
    print(f"🎯 [INTENT CLASSIFIER] Belirlenen niyet: '{intent}'")
    
    return intent

def router_node(state: GraphState) -> GraphState:
    print(f"🚦 [ROUTER] Router node başladı")
    print(f"🚦 [ROUTER] State keys: {list(state.keys())}")
    
    user_msg = state["messages"][-1]["content"]
    history_text = state.get("history_text") or ""
    
    print(f"🚦 [ROUTER] Kullanıcı mesajı: '{user_msg}'")
    print(f"🚦 [ROUTER] Geçmiş metin: '{history_text[:200]}...' (ilk 200 karakter)")
    
    state["intent"] = classify_intent(user_msg, history_text)
    
    print(f"🚦 [ROUTER] Router tamamlandı, intent: '{state['intent']}'")
    return state

def fmb_agent_node(state: GraphState) -> GraphState:
    print(f"🤖 [FMB AGENT] FMB Agent node başladı")
    
    query = state["messages"][-1]["content"]
    history_text = state.get("history_text") or ""
    
    print(f"🤖 [FMB AGENT] İşlenecek sorgu: '{query}'")
    
    # RAG belgelerini al
    print(f"🤖 [FMB AGENT] RAG belgeleri aranıyor...")
    docs = search_fmb_docs.invoke({"query": query, "k": 6})
    state["context_docs"] = docs
    print(f"🤖 [FMB AGENT] RAG'den {len(docs)} doküman alındı")
    
    # Web araması için sorguyu optimize et
    print(f"🤖 [FMB AGENT] Web arama sorgusu optimize ediliyor...")
    optimized_query = optimize_search_query.invoke({"user_query": query, "history_text": history_text})
    
    # Web'den ek bilgi ara
    print(f"🤖 [FMB AGENT] Web araması yapılıyor...")
    web_results = web_search.invoke({"query": optimized_query, "max_results": 3})
    print(f"🤖 [FMB AGENT] Web araması sonucu: {web_results}")
    state["web_results"] = web_results
    print(f"🤖 [FMB AGENT] Web'den {len(web_results)} sonuç alındı")
    
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

    # Tüm bilgileri birleştir
    docs_content = "\n\n".join(docs) if docs else ""
    web_content = "\n\n".join(web_results) if web_results else ""
    history_text = state.get("history_text") or ""
    
    print(f"🤖 [FMB AGENT] Belgeler uzunluğu: {len(docs_content)} karakter")
    print(f"🤖 [FMB AGENT] Web içerik uzunluğu: {len(web_content)} karakter")
    print(f"🤖 [FMB AGENT] Geçmiş uzunluğu: {len(history_text)} karakter")
    
    combined_context = f"Yerel Belgeler:\n{docs_content}\n\nWeb Bilgileri:\n{web_content}\n\nSohbet Geçmişi:\n{history_text}".strip()
    print(f"🤖 [FMB AGENT] Birleştirilmiş context uzunluğu: {len(combined_context)} karakter")

    formatted_prompt = MAIN_PROMPT.format(context=combined_context, question=query)
    print(f"🤖 [FMB AGENT] LLM'e gönderilen prompt uzunluğu: {len(formatted_prompt)} karakter")
    
    print(f"🤖 [FMB AGENT] LLM çağrısı yapılıyor...")
    answer = llm.invoke(formatted_prompt).content
    print(f"🤖 [FMB AGENT] LLM yanıtı alındı, uzunluk: {len(answer)} karakter")
    print(f"🤖 [FMB AGENT] LLM yanıtı: '{answer[:200]}...' (ilk 200 karakter)")
    
    state["messages"].append({"role": "assistant", "content": answer})
    print(f"🤖 [FMB AGENT] FMB Agent node tamamlandı")
    return state

def general_agent_node(state: GraphState) -> GraphState:
    print(f"💬 [GENERAL AGENT] General Agent node başladı")
    
    query = state["messages"][-1]["content"]
    print(f"💬 [GENERAL AGENT] İşlenecek sorgu: '{query}'")
    
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    
    print(f"💬 [GENERAL AGENT] LLM çağrısı yapılıyor...")
    answer = llm.invoke(query).content
    print(f"💬 [GENERAL AGENT] LLM yanıtı alındı, uzunluk: {len(answer)} karakter")
    print(f"💬 [GENERAL AGENT] LLM yanıtı: '{answer[:200]}...' (ilk 200 karakter)")
    
    state["messages"].append({"role": "assistant", "content": answer})
    print(f"💬 [GENERAL AGENT] General Agent node tamamlandı")
    return state

def build_graph():
    print(f"🏗️ [GRAPH BUILDER] Graph oluşturuluyor...")
    
    g = StateGraph(GraphState)
    g.add_node("router", router_node)
    g.add_node("fmb_agent", fmb_agent_node)
    g.add_node("general_agent", general_agent_node)
    g.set_entry_point("router")

    def route_decider(state: GraphState):
        route = "to_fmb" if state["intent"] == "fmb" else "to_general"
        print(f"🔀 [ROUTE DECIDER] Intent: '{state['intent']}' -> Route: '{route}'")
        return route

    g.add_conditional_edges(
        "router",
        route_decider,
        {"to_fmb": "fmb_agent", "to_general": "general_agent"},
    )
    g.add_edge("fmb_agent", END)
    g.add_edge("general_agent", END)
    
    compiled_graph = g.compile()
    print(f"🏗️ [GRAPH BUILDER] Graph başarıyla oluşturuldu ve derlendi")
    return compiled_graph

graph = build_graph()

def invoke_graph(user_input: str, history_text: str) -> str:
    print(f"🚀 [INVOKE GRAPH] Graph çağrısı başladı")
    print(f"🚀 [INVOKE GRAPH] Kullanıcı girişi: '{user_input}'")
    print(f"🚀 [INVOKE GRAPH] Geçmiş metin uzunluğu: {len(history_text)} karakter")
    
    initial = {
        "messages": [{"role": "user", "content": user_input}],
        "intent": None,
        "context_docs": None,
        "web_results": None,
        "history_text": history_text
    }
    
    print(f"🚀 [INVOKE GRAPH] Initial state: {list(initial.keys())}")
    print(f"🚀 [INVOKE GRAPH] Graph invoke ediliyor...")
    
    result = graph.invoke(initial)
    
    print(f"🚀 [INVOKE GRAPH] Graph tamamlandı")
    print(f"🚀 [INVOKE GRAPH] Result keys: {list(result.keys())}")
    print(f"🚀 [INVOKE GRAPH] Messages sayısı: {len(result['messages'])}")
    
    final_answer = result["messages"][-1]["content"]
    print(f"🚀 [INVOKE GRAPH] Final answer uzunluğu: {len(final_answer)} karakter")
    print(f"🚀 [INVOKE GRAPH] Final answer: '{final_answer[:200]}...' (ilk 200 karakter)")
    
    return final_answer