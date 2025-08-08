import os

def load_prompt(file_path: str) -> str:
    """Prompt dosyasını yükle"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt dosyası bulunamadı: {file_path}")
    except Exception as e:
        raise Exception(f"Prompt dosyası yüklenirken hata: {e}") 