import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import hashlib
from config import OPENAI_API_KEY

class VectorStore:
    """Vector store yönetimi"""
    
    def __init__(self, index_path: str = "vector/index"):
        self.index_path = index_path
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        # Daha iyi chunking stratejisi
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Daha küçük chunk'lar
            chunk_overlap=200,  # Daha az overlap
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]  # Daha iyi separator'lar
        )
    
    def load_documents(self, data_dir: str = "data") -> List:
        """Dokümanları yükle"""
        documents = []
        
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            
            if filename.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                # Metadata ekle
                for doc in docs:
                    doc.metadata.update({
                        'source': filename,
                        'file_type': 'pdf',
                        'chunk_id': hashlib.md5(f"{filename}_{doc.page_content[:50]}".encode()).hexdigest()[:8]
                    })
                    print(f"pdf dosyası yüklendi: {filename}")
                documents.extend(docs)
            elif filename.endswith('.txt'):
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
                # Metadata ekle
                for doc in docs:
                    doc.metadata.update({
                        'source': filename,
                        'file_type': 'text',
                        'chunk_id': hashlib.md5(f"{filename}_{doc.page_content[:50]}".encode()).hexdigest()[:8]
                    })
                    print(f"txt dosyası yüklendi: {filename}")
                documents.extend(docs)
        
        return documents
    
    def split_documents(self, documents: List) -> List:
        """Dokümanları parçala ve metadata'yı koru"""
        split_docs = self.text_splitter.split_documents(documents)
        
        # Her chunk için metadata'yı güncelle
        for i, doc in enumerate(split_docs):
            doc.metadata.update({
                'chunk_index': i,
                'total_chunks': len(split_docs),
                'chunk_size': len(doc.page_content)
            })
        
        return split_docs
    
    def create_index(self, documents: List):
        """Vector index oluştur"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        print(f"�� {len(documents)} doküman parçalanıyor...")
        split_docs = self.split_documents(documents)
        print(f"🔪 {len(split_docs)} chunk oluşturuldu")
        
        # Chunk'ları göster
        for i, doc in enumerate(split_docs[:5]):  # İlk 5 chunk'ı göster
            print(f"Chunk {i+1}: {doc.page_content[:100]}... (Metadata: {doc.metadata})")
        
        vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        vectorstore.save_local(self.index_path)
        
        print(f"✅ Vector index oluşturuldu: {self.index_path}")
        return vectorstore
    
    def load_index(self):
        """Mevcut index'i yükle"""
        if os.path.exists(self.index_path):
            return FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            raise FileNotFoundError(f"Index bulunamadı: {self.index_path}")
    
    def get_retriever(self, k: int = 5):
        """Retriever döndür"""
        vectorstore = self.load_index()
        return vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance kullan
            search_kwargs={
                "k": k,
                "fetch_k": k * 3,  # Daha fazla doküman fetch et
                "lambda_mult": 0.7,  # Diversity vs relevance balance
                "filter": None  # İleride filtreleme için
            }
        )
    
    def similarity_search_with_score(self, query: str, k: int = 5):
        """Score'larla birlikte similarity search"""
        vectorstore = self.load_index()
        return vectorstore.similarity_search_with_score(query, k=k)
