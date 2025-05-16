import easyocr
from typing import List, Dict

reader = easyocr.Reader(['pt', 'en'])

def extract_text_from_image(image_bytes: bytes) -> List[Dict]:
    # Utiliza EasyOCR para extrair texto e bounding boxes da imagem
    # Retorna lista de dicts com texto e posição
    results = reader.readtext(image_bytes)
    structured = []
    for (bbox, text, conf) in results:
        structured.append({
            "bbox": bbox,
            "text": text,
            "confidence": conf
        })
    return structured