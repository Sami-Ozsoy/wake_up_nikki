#!/usr/bin/env python3
"""
Vector index'i yeniden oluşturma script'i
"""

from vector.vector_store import VectorStore
import os

def rebuild_index():
    """Vector index'i yeniden oluştur"""
    print("🔄 Vector index yeniden oluşturuluyor...")
    
    # Vector store instance'ı oluştur
    vector_store = VectorStore()
    
    # Dokümanları yükle
    documents = vector_store.load_documents("data")
    print(f"📄 {len(documents)} doküman yüklendi")
    
    # Index'i oluştur
    vector_store.create_index(documents)
    
    print("✅ Vector index başarıyla yeniden oluşturuldu!")

if __name__ == "__main__":
    rebuild_index()
