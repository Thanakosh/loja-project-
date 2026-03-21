import asyncio
import json
import os
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, get_async_engine
from app.models import *
from app.models.ncm import NCM


async def import_ncms():
    json_path = os.path.abspath(r"C:\Users\usuario\Downloads\Tabela_NCM_Vigente_20260221.json")

    if not os.path.exists(json_path):
        print(f"Erro: Arquivo nÃ£o encontrado: {json_path}")
        return

    print("Carregando arquivo JSON...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    capitulos_relevantes = ("39", "73", "82", "83", "84", "85", "94")

    ncms_to_insert = []

    print("Filtrando NCMs relevantes...")
    for item in data.get("Nomenclaturas", []):
        codigo_formatado = item["Codigo"].replace(".", "")

        if len(codigo_formatado) == 8 and codigo_formatado.isdigit():
            if codigo_formatado.startswith(capitulos_relevantes):
                ncms_to_insert.append(
                    NCM(codigo=codigo_formatado, descricao=item["Descricao"])
                )

    print(f"Encontrados {len(ncms_to_insert)} NCMs de interesse.")

    if not ncms_to_insert:
        print("Nenhum NCM encontrado. Verifique o arquivo.")
        return

    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as db:
        try:
            print("Limpando NCMs antigos...")
            await db.execute(NCM.__table__.delete())

            print("Salvando no banco de dados...")
            db.add_all(ncms_to_insert)
            await db.commit()
            print("ImportaÃ§Ã£o concluÃ­da com sucesso!")

        except Exception as e:
            await db.rollback()
            print(f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    asyncio.run(import_ncms())
