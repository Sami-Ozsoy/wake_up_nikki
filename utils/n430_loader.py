from typing import List

from langchain.schema import Document
from unstructured.partition.pdf import partition_pdf


def load_n430_params(pdf_path: str) -> List[Document]:
    """
    N430 Parametre Listesi PDF'ini tablo-bilinçli şekilde yükler.

    Her tablo satırını (parametre) ayrı bir Document olarak döndürür ve
    alan-bazlı metadata ekler.
    """
    elements = partition_pdf(pdf_path, strategy="fast")
    documents: List[Document] = []

    current_page = 1
    for element in elements:
        # Sayfa numarasını güncelle
        if getattr(element, "metadata", None) and getattr(element.metadata, "page_number", None):
            current_page = element.metadata.page_number

        # Sadece tabloları işle
        if getattr(element, "category", None) != "Table":
            continue

        table_md = element.text or ""
        # Basit Markdown tablo ayrıştırma: ilk satır başlık, ikinci satır ayırıcı
        lines = [line for line in table_md.splitlines() if "|" in line]
        if len(lines) < 2:
            continue

        # Başlıkları normalize et
        header_cells = [h.strip().lower() for h in lines[0].split("|") if h.strip()]

        # Veri satırları (çoğunlukla 2. satır ayırıcı olur)
        data_rows = lines[2:] if len(lines) > 2 else []
        for row in data_rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if not cells:
                continue

            row_map = {header_cells[i]: cells[i] for i in range(min(len(header_cells), len(cells)))}

            param_name = row_map.get("param") or row_map.get("name") or row_map.get("parameter") or ""
            description = row_map.get("description") or row_map.get("açıklama") or ""
            group = row_map.get("group") or row_map.get("kategori") or ""
            sms_format = row_map.get("sms") or row_map.get("command") or row_map.get("komut") or ""
            default = row_map.get("default") or row_map.get("varsayılan") or ""
            value_range = row_map.get("range") or row_map.get("aralık") or ""
            unit = row_map.get("unit") or row_map.get("birim") or ""

            # Gömme metni tutarlı sırada üret
            text = " | ".join([
                f"param_name: {param_name}",
                f"group: {group}",
                f"description: {description}",
                f"sms_format: {sms_format}",
                f"default: {default}",
                f"range: {value_range}",
                f"unit: {unit}",
            ])

            metadata = {
                "source": "N430 Parametre Listesi.pdf",
                "file_type": "pdf",
                "device": "N430",
                "page": current_page,
                "param_name": param_name,
                "group": group,
                "has_sms_format": bool(sms_format),
                "default": default,
                "range": value_range,
                "unit": unit,
            }

            documents.append(Document(page_content=text, metadata=metadata))

    return documents


