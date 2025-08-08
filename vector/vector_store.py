import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

class VectorStore:
    """Vector store yönetimi"""
    
    def __init__(self, index_path: str = "vector/index"):
        self.index_path = index_path
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def load_documents(self, data_dir: str = "data") -> List:
        """Dokümanları yükle"""
        documents = []
        
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            
            if filename.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith('.txt'):
                loader = TextLoader(file_path, encoding='utf-8')
                documents.extend(loader.load())
        
        return documents
    
    def split_documents(self, documents: List) -> List:
        """Dokümanları parçala"""
        return self.text_splitter.split_documents(documents)
    
    def create_index(self, documents: List):
        """Vector index oluştur"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        vectorstore = FAISS.from_documents(documents, self.embeddings)
        vectorstore.save_local(self.index_path)
        
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
        return vectorstore.as_retriever(search_kwargs={"k": k}) 