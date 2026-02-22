"""
Script de matching automatico de NCM
"""
import sqlite3
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rapidfuzz import fuzz, process
    FUZZY_OK = True
except ImportError:
    print("Aviso: rapidfuzz nao instalado, pulando fuzzy matching")
    FUZZY_OK = False

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "loja.db"))

REGRAS = [
    # LAMPADAS
    (["lampada", "led"],          [],                  "85393090"),
    (["lampada", "fluor"],        [],                  "85393090"),
    (["lampada", "espiral"],      [],                  "85393090"),
    (["lampada", "halog"],        [],                  "85392190"),
    (["lampada", "vapor"],        [],                  "85393090"),
    (["lampada", "bolinha"],      [],                  "85392990"),
    (["lampada", "palito"],       [],                  "85392990"),
    (["lampada"],                 [],                  "85392990"),
    (["lampara"],                 [],                  "85392990"),

    # ILUMINACAO
    (["luminaria", "led"],        [],                  "94054090"),
    (["luminaria"],               [],                  "94054090"),
    (["plafon", "led"],           [],                  "94054090"),
    (["plafon"],                  [],                  "94054090"),
    (["spot", "led"],             [],                  "94054090"),
    (["spot"],                    [],                  "94054090"),
    (["refletor", "led"],         [],                  "94054090"),
    (["refletor"],                [],                  "94054090"),
    (["pendente"],                [],                  "94054090"),
    (["arandela"],                [],                  "94054090"),
    (["abajur"],                  [],                  "94059090"),
    (["lustre"],                  [],                  "94054090"),
    (["fita", "led"],             [],                  "94054090"),

    # FIOS E CABOS
    (["cabo", "flexivel"],        [],                  "85444900"),
    (["cabo", "pp"],              [],                  "85444900"),
    (["fio", "solido"],           [],                  "85444900"),
    (["fio", "flexivel"],         [],                  "85444900"),
    (["condutor"],                [],                  "85444900"),
    (["fio"],                     ["dental","arame"],  "85444900"),
    (["cabo"],                    ["tv","hdmi","usb","rede","dados"], "85444900"),
    (["extensao"],                [],                  "85444900"),

    # FITAS
    (["fita", "isolante"],        [],                  "85329000"),
    (["fita", "auto", "fusao"],   [],                  "85329000"),
    (["fita", "auto-fusao"],      [],                  "85329000"),
    (["fita", "eletrica"],        [],                  "85329000"),

    # DISJUNTORES E PROTECAO
    (["disjuntor"],               [],                  "85362000"),
    (["dps"],                     [],                  "85363090"),
    (["fusivel"],                 [],                  "85361000"),
    (["rele", "foto"],            [],                  "85364900"),
    (["rele"],                    [],                  "85364900"),
    (["fotocelula"],              [],                  "85364900"),
    (["minuteria"],               [],                  "85364900"),
    (["dimmer"],                  [],                  "85363090"),

    # TOMADAS E INTERRUPTORES
    (["tomada"],                  [],                  "85369090"),
    (["interruptor"],             [],                  "85369090"),
    (["benjamim"],                [],                  "85369090"),
    (["adaptador"],               ["hdmi","usb"],      "85369090"),

    # QUADROS
    (["quadro", "distrib"],       [],                  "85371090"),
    (["centro", "distr"],         [],                  "85371090"),
    (["barramento"],              [],                  "85371090"),
    (["painel", "eletric"],       [],                  "85371090"),

    # ELETRODUTOS
    (["eletroduto", "pvc"],       [],                  "39173290"),
    (["eletroduto", "metal"],     [],                  "73063090"),
    (["eletroduto"],              [],                  "39173290"),
    (["condulete"],               [],                  "85369090"),
    (["canaleta"],                [],                  "39259090"),
    (["calha", "cabo"],           [],                  "39259090"),

    # ABRACADEIRAS
    (["abracadeira", "nylon"],    [],                  "39269090"),
    (["abracadeira", "plast"],    [],                  "39269090"),
    (["abracadeira", "metal"],    [],                  "73269090"),
    (["abracadeira"],             [],                  "39269090"),

    # CONECTORES
    (["conector"],                [],                  "85369090"),
    (["borne"],                   [],                  "85369090"),

    # SENSORES
    (["sensor", "presenca"],      [],                  "85311090"),
    (["sensor", "movim"],         [],                  "85311090"),
    (["sensor"],                  [],                  "85311090"),
    (["temporizador"],            [],                  "91059900"),

    # ESTABILIZADORES
    (["estabilizador"],           [],                  "85044090"),
    (["nobreak"],                 [],                  "85044090"),

    # FERRAMENTAS ELETRICAS
    (["furadeira"],               [],                  "84672900"),
    (["parafusadeira"],           [],                  "84672900"),
    (["esmerilhadeira"],          [],                  "84672900"),
    (["pistola", "cola"],         [],                  "84672900"),

    # FERRAMENTAS MANUAIS
    (["alicate"],                 [],                  "82031000"),
    (["chave", "fenda"],          [],                  "82055900"),
    (["chave", "philips"],        [],                  "82055900"),
    (["chave", "teste"],          [],                  "82055900"),
    (["martelo"],                 [],                  "82051000"),
    (["estilete"],                [],                  "82119200"),
    (["lamina", "estilete"],      [],                  "82119200"),
    (["trena"],                   [],                  "90261000"),
    (["multimetro"],              [],                  "90303900"),
    (["amperimetro"],             [],                  "90281000"),
    (["arco", "serra"],           [],                  "82029900"),

    # HIDRAULICA
    (["joelho", "esgoto"],        [],                  "39172390"),
    (["joelho", "aqua"],          [],                  "39172390"),
    (["joelho", "pvc"],           [],                  "39172390"),
    (["joelho"],                  [],                  "39172390"),
    (["juncao", "esgoto"],        [],                  "39172390"),
    (["juncao"],                  [],                  "39172390"),
    (["tubo", "pvc"],             [],                  "39172290"),
    (["cano", "pvc"],             [],                  "39172290"),
    (["registro"],                ["fiscal","nf"],     "84818090"),
    (["torneira"],                [],                  "84818010"),
    (["valvula"],                 [],                  "84818090"),
    (["sifao"],                   [],                  "39249090"),
    (["assento"],                 [],                  "39249090"),
    (["ducha"],                   [],                  "84818010"),
    (["chuveiro"],                [],                  "85162100"),
    (["aquecedor", "agua"],       [],                  "85162100"),
    (["veda"],                    [],                  "38249990"),
    (["plug", "pvc"],             [],                  "39172390"),
    (["bico", "torneira"],        [],                  "84818010"),
    (["anel", "borracha"],        [],                  "40169300"),

    # PARAFUSOS E FIXACAO
    (["parafuso"],                [],                  "73181590"),
    (["porca"],                   [],                  "73181600"),
    (["arruela"],                 [],                  "73182900"),
    (["bucha"],                   [],                  "39269090"),

    # ANTENAS E CFTV
    (["antena"],                  [],                  "85291090"),
    (["balun"],                   [],                  "85291090"),
    (["camera", "cftv"],          [],                  "85258090"),
    (["camera"],                  [],                  "85258090"),

    # OUTROS
    (["suporte", "tv"],           [],                  "94039090"),
    (["haste", "aterr"],          [],                  "76169000"),
    (["bateria"],                 [],                  "85072000"),
    (["arame"],                   [],                  "73170000"),
]


def normalizar(texto):
    t = texto.lower()
    for a, b in [("á","a"),("à","a"),("ã","a"),("â","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ü","u"),("ç","c")]:
        t = t.replace(a, b)
    return re.sub(r'[^a-z0-9 ]', ' ', t)


def aplicar_regras(nome_norm):
    for palavras_sim, palavras_nao, ncm in REGRAS:
        if all(p in nome_norm for p in palavras_sim):
            if not any(p in nome_norm for p in palavras_nao):
                return ncm
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome FROM produto
        WHERE ativo = 1 AND (codigo_ncm IS NULL OR codigo_ncm = '' OR length(codigo_ncm) < 8)
        ORDER BY nome
    """)
    produtos = cur.fetchall()

    cur.execute("SELECT codigo, descricao FROM ncm")
    ncms = cur.fetchall()
    ncm_dict = {c: d for c, d in ncms}

    print(f"Produtos sem NCM: {len(produtos)}")
    print(f"NCMs no banco:    {len(ncms)}")
    print("=" * 60)

    por_regra = []
    por_fuzzy = []
    sem_match = []

    for pid, nome in produtos:
        nome_norm = normalizar(nome)
        ncm = aplicar_regras(nome_norm)
        if ncm:
            por_regra.append((pid, nome, ncm))
            continue

        if FUZZY_OK:
            descricoes = [normalizar(n[1]) for n in ncms]
            resultado = process.extractOne(nome_norm, descricoes, scorer=fuzz.token_set_ratio)
            if resultado and resultado[1] >= 72:
                ncm_fuzzy = ncms[resultado[2]][0]
                por_fuzzy.append((pid, nome, ncm_fuzzy, resultado[1]))
                continue

        sem_match.append((pid, nome))

    print(f"Resolvidos por regra:      {len(por_regra)}")
    print(f"Resolvidos por similaridade: {len(por_fuzzy)}")
    print(f"Sem match (revisao manual):  {len(sem_match)}")
    print()

    print("Salvando no banco...")
    for pid, nome, ncm in por_regra:
        cur.execute("UPDATE produto SET codigo_ncm = ? WHERE id = ?", (ncm, pid))
    for pid, nome, ncm, score in por_fuzzy:
        cur.execute("UPDATE produto SET codigo_ncm = ? WHERE id = ?", (ncm, pid))
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM produto WHERE ativo=1 AND codigo_ncm IS NOT NULL AND codigo_ncm != '' AND length(codigo_ncm)=8")
    com_ncm = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM produto WHERE ativo=1 AND (codigo_ncm IS NULL OR codigo_ncm='' OR length(codigo_ncm)<8)")
    sem_ncm = cur.fetchone()[0]
    total = com_ncm + sem_ncm

    print("=" * 60)
    print("RESULTADO FINAL:")
    print(f"  Com NCM : {com_ncm} ({com_ncm/total*100:.1f}%)")
    print(f"  Sem NCM : {sem_ncm} ({sem_ncm/total*100:.1f}%)")

    if sem_match:
        print(f"\nProdutos para revisao manual ({len(sem_match)}):")
        for pid, nome in sem_match[:40]:
            print(f"  ID {pid}: {nome}")
        if len(sem_match) > 40:
            print(f"  ... e mais {len(sem_match)-40}")

    conn.close()

if __name__ == "__main__":
    main()
