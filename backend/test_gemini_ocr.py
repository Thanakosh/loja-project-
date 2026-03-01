import os
import sys
import json
from google import genai
from google.genai import types
from pydantic import ValidationError

# Adding the current directory to sys.path to import from app.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.schemas.ocr import NotaFiscalExtraida

def extrair_dados_nf(caminho_arquivo: str, api_key: str):
    print("--------------------------------------------------")
    print(f"[1] Configurando Gemini Client...")
    
    # Nova SDK: genai.Client
    client = genai.Client(api_key=api_key)

    # Use flash para notas, é rápido, barato e excelente
    model = 'gemini-2.5-flash'

    print(f"[2] Fazendo upload do arquivo: {caminho_arquivo}")
    # Faz upload do arquivo para a API do Gemini
    sample_file = client.files.upload(file=caminho_arquivo)
    
    print("[3] Processando arquivo com Inteligência Artificial...")
    
    prompt = """
    Você é um assistente especialista em ler Notas Fiscais, Cupons Fiscais e Invoices Brasileiros (NFe, NFCe, NFSe).
    Eu anexei uma imagem ou PDF de uma nota fiscal. Extraia todos os dados presentes, incluindo o fornecedor (nome e cnpj), os números identificadores,
    data de emissão e as linhas contendo todos os itens (produtos) comprados e valores totais.
    """

    try:
        # A nova SDK permite passar o Schema do Pydantic diretamente nela
        # o que garante perfeitamente que a resposta virá igualzinha a nossa classe Python!
        response = client.models.generate_content(
            model=model,
            contents=[sample_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NotaFiscalExtraida,
            ),
        )
        
        print(f"\n[4] Extração concluída. Deletando arquivo do Gemini...")
        client.files.delete(name=sample_file.name)
        
        print("\n--- Resultado JSON Raw do Gemini ---")
        print(response.text)
        print("------------------------------------\n")
        
        print("[5] Validando com Pydantic...")
        # Como passamos o "response_schema", ele tem altíssima chance de estar 100% correto
        dados_json = json.loads(response.text)
        nota_validada = NotaFiscalExtraida(**dados_json)
        
        print("\n[✔] SUCESSO! O modelo retornou os dados que foram lidos para seu schema Python:")
        print(f"Fornecedor: {nota_validada.fornecedor} (CNPJ: {nota_validada.cnpj_fornecedor})")
        print(f"Valor Total: R$ {nota_validada.valor_total}")
        print(f"Total de itens: {len(nota_validada.produtos)}")
        for idx, item in enumerate(nota_validada.produtos, start=1):
            print(f"  - Item {idx}: {item.nome} | Qtd: {item.quantidade} | R$ {item.preco_unitario} | NCM: {item.codigo_ncm}")
            
    except ValidationError as e:
        print("\n[X] Ops, o Gemini retornou sucesso, mas não respeitou os tipos do Schema Pydantic. Erro de Validação:")
        print(e)
    except Exception as e:
         print(f"\n[X] Ocorreu um erro na requisição: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Testar extração de NF Brasileira com Gemini")
    parser.add_argument("arquivo", help="Caminho para o arquivo PDF ou Imagem (Ex: nf_teste.pdf)")
    parser.add_argument("--key", help="Gemini API Key (Opcional se GEMINI_API_KEY existir)", default=os.getenv("GEMINI_API_KEY"))
    args = parser.parse_args()
    
    if not args.key:
        print("ERRO: Sua API Key não foi encontrada. Rode usando:")
        print("python test_gemini_ocr.py sua_nota.pdf --key \"AIzaSySuaChaveAqui\"")
        sys.exit(1)
        
    if not os.path.exists(args.arquivo):
        print(f"ERRO: Arquivo '{args.arquivo}' não encontrado. Você precisa colocar uma nota de verdade para eu ler!")
        sys.exit(1)
        
    extrair_dados_nf(args.arquivo, args.key)
