import json
import asyncio
import os
import sys
from sqlalchemy.orm import sessionmaker

# Ajustando o PYTHONPATH dinamicamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_engine, Base
from app.models.ncm import NCM
from app.models import *

def import_ncms():
    json_path = os.path.abspath(r"C:\Users\usuario\Downloads\Tabela_NCM_Vigente_20260221.json")
    
    if not os.path.exists(json_path):
        print(f"Erro: Arquivo não encontrado: {json_path}")
        return

    print("Carregando arquivo JSON...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filtrar apenas capítulos relevantes
    capitulos_relevantes = ("39", "73", "82", "83", "84", "85", "94")
    
    ncms_to_insert = []
    
    print("Filtrando NCMs relevantes...")
    for item in data.get("Nomenclaturas", []):
        codigo_formatado = item["Codigo"].replace(".", "")
        
        # Aceita apenas os NCMs completos (8 dígitos numéricos)
        if len(codigo_formatado) == 8 and codigo_formatado.isdigit():
            # Extrair apenas NCMs dos capítulos que queremos
            if codigo_formatado.startswith(capitulos_relevantes):
                ncms_to_insert.append(
                    NCM(codigo=codigo_formatado, descricao=item["Descricao"])
                )

    print(f"Encontrados {len(ncms_to_insert)} NCMs de interesse.")
    
    if not ncms_to_insert:
        print("Nenhum NCM encontrado. Verifique o arquivo.")
        return

    engine = get_engine()
    # Criar todas as tabelas caso não existam (útil porque o alembic falhou)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Limpando NCMs antigos...")
        db.query(NCM).delete()
        
        print("Salvando no banco de dados...")
        db.bulk_save_objects(ncms_to_insert)
        db.commit()
        print("Importação concluída com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"Ocorreu um erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_ncms()
