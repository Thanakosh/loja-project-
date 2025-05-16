import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
from typing import List, Dict, Any # Adicionado Any para flexibilidade
import uuid # Para gerar nomes de arquivo únicos

# Ajuste o caminho para a pasta de templates
# __file__ é o caminho para o arquivo pdf.py atual
# os.path.dirname(__file__) é a pasta 'services'
# os.path.join(..., '..', 'templates') sobe um nível para 'app' e entra em 'templates'
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
PDF_OUTPUT_DIR = "/tmp/orcamentos_pdf" # Pasta para salvar os PDFs dentro do container

# Certifique-se de que o diretório de saída exista
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

# Configuração do Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def gerar_pdf_orcamento(
    orcamento_data: Dict[str, Any], # Dados do cliente, etc. (ex: OrcamentoCreate.dict())
    itens_processados: List[Dict[str, Any]], # Lista de itens com nome, preço, subtotal (ex: List[OrcamentoItemRead.dict()])
    valor_total_orcamento: float,
    orcamento_id_ref: Optional[int] = None # Opcional, se o orçamento já tiver um ID no banco
) -> str:
    """
    Gera um PDF de orçamento a partir dos dados fornecidos.Args:
    orcamento_data: Dicionário com dados do orçamento (cliente, etc.).
    itens_processados: Lista de dicionários, cada um representando um item do orçamento
                       com detalhes do produto e subtotal.
    valor_total_orcamento: O valor total calculado do orçamento.
    orcamento_id_ref: ID de referência do orçamento, se houver.

Returns:
    O caminho completo para o arquivo PDF gerado.
"""
template = env.get_template("orcamento_template.html")

# Dados para passar ao template
context = {
    "orcamento": orcamento_data,
    "itens_orcamento": itens_processados,
    "valor_total": valor_total_orcamento,
    "data_emissao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    "empresa_nome": "Minha Loja Fantástica", # Você pode pegar isso de config.py no futuro
    "empresa_contato": "contato@minhaloja.com", # Idem
    "orcamento_id": orcamento_id_ref
}

html_out = template.render(context)

# Gera um nome de arquivo único para evitar sobrescrever
nome_arquivo_unico = f"orcamento_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
caminho_arquivo_pdf = os.path.join(PDF_OUTPUT_DIR, nome_arquivo_unico)

# Gera o PDF
HTML(string=html_out).write_pdf(caminho_arquivo_pdf)

return caminho_arquivo_pdf</code></pre>Explicação:TEMPLATE_DIR: Define onde o Jinja2 procurará seus templates HTML.PDF_OUTPUT_DIR: Define uma pasta /tmp/orcamentos_pdf dentro do container para salvar os PDFs gerados. A pasta /tmp é geralmente volátil (se apaga quando o container para), o que é aceitável para este MVP. Em produção, você pode querer um volume Docker persistente para isso.os.makedirs(PDF_OUTPUT_DIR, exist_ok=True): Garante que o diretório de saída exista.gerar_pdf_orcamento:Recebe os dados do orçamento, os itens já processados (com nome do produto, preço, etc., que virão do banco), o valor total e um ID de referência opcional.Carrega o orcamento_template.html.Cria um context com todos os dados que o template HTML espera.Renderiza o HTML.Cria um nome de arquivo único para o PDF.Usa HTML(string=html_out).write_pdf(caminho_arquivo_pdf) do WeasyPrint para converter o HTML em PDF e salvá-lo.Retorna o caminho completo do arquivo PDF gerado.