import re
from typing import List, Dict

def extract_key_data(ocr_results: List[Dict]) -> Dict:
    # Exemplo de parser simples: pega possíveis CNPJ, datas e valores
    data = {"cnpj": [], "dates": [], "values": []}
    for item in ocr_results:
        text = item["text"]
        # CNPJ (formato 99.999.999/9999-99)
        cnpj_matches = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text)
        data["cnpj"].extend(cnpj_matches)
        # Datas (formato dd/mm/aaaa)
        date_matches = re.findall(r'\d{2}/\d{2}/\d{4}', text)
        data["dates"].extend(date_matches)
        # Valores (R$ 1.234,56)
        value_matches = re.findall(r'R\$ ?[\d\.,]+', text)
        data["values"].extend(value_matches)
    return data