"""Tabela CEST — Código Especificador da Substituição Tributária.

Fonte: Convênio ICMS 142/2018 (anexos I a XXIX).
A tabela completa possui ~900 itens. Aqui estão os ~180 mais comuns
no varejo brasileiro.

Formato: 7 dígitos numéricos (XX.XXX.XX), armazenados sem pontos.
Estrutura:  SS.GGG.II
  SS  = Segmento (01 a 29)
  GGG = Grupo dentro do segmento
  II  = Item dentro do grupo
"""

from __future__ import annotations

from typing import List, Tuple

# Segmentos do CEST (para referência)
SEGMENTOS_CEST: dict[str, str] = {
    "01": "Autopeças",
    "02": "Bebidas alcoólicas, exceto cerveja e chope",
    "03": "Cervejas, chopes, refrigerantes, águas e outras bebidas",
    "04": "Cigarros e outros produtos derivados do fumo",
    "05": "Cimentos",
    "06": "Combustíveis e lubrificantes",
    "07": "Energia elétrica",
    "08": "Ferramentas",
    "09": "Lâmpadas, reatores e starters",
    "10": "Materiais de construção e congêneres",
    "11": "Materiais de limpeza",
    "12": "Materiais elétricos",
    "13": "Medicamentos de uso humano e outros produtos farmacêuticos",
    "14": "Papéis, plásticos, produtos cerâmicos e vidros",
    "15": "Pneumáticos, câmaras de ar e protetores",
    "16": "Produtos alimentícios",
    "17": "Produtos de papelaria",
    "18": "Produtos de perfumaria e de higiene pessoal e cosméticos",
    "19": "Produtos eletrônicos, eletroeletrônicos e eletrodomésticos",
    "20": "Rações para animais domésticos",
    "21": "Sorvetes e preparados para fabricação de sorvetes",
    "22": "Tintas e vernizes",
    "23": "Veículos automotores",
    "24": "Veículos de duas e três rodas motorizados",
    "25": "Venda de mercadorias pelo sistema porta a porta",
    "26": "Artefatos de uso doméstico",
    "27": "Máquinas e aparelhos mecânicos, elétricos, eletromecânicos e automáticos",
    "28": "Produtos de telecomunicações",
}

# CEST: código (7 dígitos sem pontos) → descrição
CEST_VAREJO: dict[str, str] = {
    # ═══ 01 — Autopeças ═══
    "0100100": "Catalizadores em colméia cerâmica ou metálica para conversão catalítica de gases de escape de veículos",
    "0100200": "Tubos e seus acessórios de uso automotivo",
    "0100500": "Protetores de caçamba de uso automotivo",
    "0100800": "Molas e folhas de molas de uso automotivo",
    "0101200": "Juntas, gaxetas de uso automotivo",
    "0101700": "Partes de trens de rolamento de uso automotivo",
    "0102200": "Filtros de uso automotivo",
    "0102500": "Palhetas e limpadores de para-brisa",
    "0102700": "Defletores de ar de uso automotivo",
    "0103100": "Discos de fricção (embreagem) de uso automotivo",
    "0103600": "Baterias (acumuladores) de chumbo para uso automotivo",
    "0104100": "Velas de ignição de uso automotivo",
    "0104400": "Cintas e correias de uso automotivo",
    "0104900": "Pneus recauchutados de uso automotivo",
    "0105200": "Retrovisores de uso automotivo",
    "0105500": "Lentes de faróis, de lanternas e outros de uso automotivo",
    "0106200": "Tapetes de uso automotivo",
    "0107000": "Cabos de vela de ignição e outros condutores elétricos de uso automotivo",
    "0107600": "Frisos, decalques e molduras de uso automotivo",
    "0108200": "Alto-falantes de uso automotivo",

    # ═══ 03 — Bebidas ═══
    "0300100": "Água mineral, gasosa ou não, ou potável, naturais, em garrafa",
    "0300200": "Água mineral, gasosa ou não, potável, naturais em embalagens ≤ 10L",
    "0300300": "Água mineral, gasosa ou não, potável, naturais em embalagens de 10L a 20L",
    "0300400": "Água mineral, gasosa ou não, potável, naturais em embalagens ≥ 20L",
    "0300500": "Outras águas minerais, potável",
    "0300600": "Águas gaseificadas artificialmente",
    "0300700": "Refrigerantes em garrafa com capacidade de até 600 ml",
    "0300800": "Refrigerantes em garrafa com capacidade de 600 ml até 2L",
    "0300900": "Refrigerantes em garrafa com capacidade acima de 2L",
    "0301000": "Refrigerantes em lata",
    "0301100": "Refrigerantes em embalagem PET",
    "0301200": "Xaropes e concentrados para refrigerantes — pré-mix e post-mix",
    "0301300": "Cerveja sem álcool",
    "0301400": "Bebidas energéticas",
    "0301500": "Bebidas hidroeletrolíticas (isotônicas)",
    "0301600": "Outras bebidas não alcoólicas",
    "0301700": "Cerveja em garrafa de vidro retornável",
    "0301800": "Cerveja em garrafa de vidro descartável",
    "0301900": "Cerveja em lata",
    "0302000": "Cerveja em barril",
    "0302100": "Chope",
    "0302200": "Cerveja em garrafa PET",

    # ═══ 06 — Combustíveis ═══
    "0600100": "Álcool etílico não desnaturado, com teor alcoólico ≥ 80% — etanol combustível",
    "0600200": "Gasolina automotiva A, exceto premium",
    "0600300": "Gasolina automotiva C, exceto premium",
    "0600500": "Gasolina automotiva A premium",
    "0600600": "Gasolina automotiva C premium",
    "0600700": "Óleo diesel A (exceto S10)",
    "0600800": "Óleo diesel B (exceto S10)",
    "0601000": "Óleo diesel A S10",
    "0601100": "Óleo diesel B S10",
    "0601300": "Gás liquefeito de petróleo (GLP), inclusive misturas",
    "0601500": "Gás natural veicular (GNV)",

    # ═══ 11 — Materiais de Limpeza ═══
    "1100100": "Água sanitária, alvejantes e outros",
    "1100200": "Odorizantes / desodorizantes de ambiente e superfícies",
    "1100300": "Sabões em barra, pedaços e figuras moldadas",
    "1100400": "Sabões em pó, flocos, lâminas e grãos",
    "1100500": "Detergentes líquidos para lavagem de louça",
    "1100600": "Detergentes líquidos para lavagem de roupa",
    "1100700": "Desinfetantes",
    "1100800": "Amaciantes e suavizantes de tecidos",
    "1100900": "Esponjas para limpeza",
    "1101000": "Álcool etílico para limpeza",
    "1101100": "Outros produtos de limpeza não especificados",

    # ═══ 13 — Medicamentos e Farmacêuticos ═══
    "1300100": "Medicamentos de referência — positiva",
    "1300200": "Medicamentos de referência — negativa",
    "1300300": "Medicamentos de referência — neutra",
    "1300400": "Medicamentos genéricos — positiva",
    "1300500": "Medicamentos genéricos — negativa",
    "1300600": "Medicamentos genéricos — neutra",
    "1300700": "Medicamentos similares — positiva",
    "1300800": "Medicamentos similares — negativa",
    "1300900": "Medicamentos similares — neutra",
    "1301000": "Outros medicamentos — positiva",
    "1301100": "Outros medicamentos — negativa",
    "1301200": "Outros medicamentos — neutra",

    # ═══ 16 — Produtos Alimentícios ═══
    "1600100": "Chocolate branco, em embalagens de conteúdo ≤ 1 kg",
    "1600200": "Chocolates contendo cacau, em embalagens de conteúdo ≤ 1 kg",
    "1600300": "Chocolate em barras, tabletes ou blocos ou no estado líquido em recipientes ≤ 2 kg",
    "1600400": "Chocolates e outras preparações contendo cacau, em embalagens ≤ 1 kg",
    "1600500": "Achocolatados em pó em embalagens ≤ 1 kg",
    "1600600": "Cacao em pó — sem adição de açúcar ou edulcorante",
    "1600700": "Balas, caramelos, confeitos, pastilhas e semelhantes — sem cacau",
    "1600800": "Gomas de mascar",
    "1600900": "Bombons, inclusive à base de chocolate branco, sem cacau",
    "1601000": "Barras de cereais",
    "1601100": "Suplementos alimentares e compostos apresentados em forma de alimentos",
    "1601200": "Café torrado e moído em embalagens ≤ 2 kg",
    "1601300": "Café torrado em grãos em embalagens ≤ 2 kg",
    "1601400": "Café solúvel",
    "1601500": "Mate, inclusive mate solúvel e concentrado",
    "1602000": "Sardinha em conserva",
    "1602100": "Atum em conserva",
    "1602200": "Filés e outras carnes de peixe em conserva",
    "1602500": "Pão industrializado, inclusive pão de forma",
    "1602600": "Bolo industrializado e produtos de panificação não especificados",
    "1602700": "Biscoito e bolacha derivados de farinha de trigo (exceto dos tipos cream cracker, água e sal, maisena e maria)",
    "1602800": "Biscoitos dos tipos cream cracker, água e sal, maisena e maria",
    "1603000": "Macarrão instantâneo",
    "1603100": "Massas alimentícias — outros tipos",
    "1603500": "Molhos de tomate em embalagens ≤ 1 kg",
    "1603600": "Molhos de tomate em embalagens > 1 kg",
    "1603700": "Condimentos e temperos compostos, incluindo molho de pimenta",
    "1603800": "Maionese em embalagens ≤ 650 g",
    "1604000": "Margarina e creme vegetal em embalagens ≤ 500 g",
    "1604100": "Margarina e creme vegetal em embalagens de 500 g a 1 kg",
    "1604200": "Margarina e creme vegetal em embalagens > 1 kg",
    "1604400": "Óleos vegetais comestíveis em embalagens ≤ 5 litros",
    "1604600": "Vinagres em embalagens ≤ 1 litro",
    "1604700": "Leite UHT (longa vida) em recipientes ≤ 2 litros",
    "1604800": "Leite em pó em embalagens ≤ 2,5 kg",
    "1604900": "Queijos tipo mussarela, minas, prato e parmesão",
    "1605000": "Iogurte e leite fermentado em embalagens ≤ 2 kg",
    "1605100": "Requeijão e similares em embalagens ≤ 500 g",
    "1605200": "Manteiga em embalagens ≤ 1 kg",
    "1605300": "Açúcar refinado, cristal, demerara, outros — embalagens ≤ 2 kg",
    "1605400": "Arroz em embalagens ≤ 5 kg",
    "1605500": "Feijão em embalagens ≤ 5 kg",
    "1605600": "Farinhas de mandioca, de milho e outras — embalagens ≤ 5 kg",

    # ═══ 18 — Perfumaria e Higiene ═══
    "1800100": "Sabonetes de toucador",
    "1800200": "Produtos para barbear (exceto os de lâmina)",
    "1800300": "Desodorantes e antiperspirantes",
    "1800400": "Dentifrícios (cremes dentais)",
    "1800500": "Fios e fitas dentais",
    "1800600": "Enxaguatórios bucais",
    "1800700": "Xampus para o cabelo",
    "1800800": "Condicionadores para o cabelo",
    "1800900": "Tintas para o cabelo e depilatórios",
    "1801000": "Laquê, fixadores e modeladores para o cabelo",
    "1801100": "Cremes de beleza, cremes hidratantes e loções",
    "1801200": "Protetores e bloqueadores solares",
    "1801300": "Maquiagem e preparações de beleza",
    "1801400": "Lenços umedecidos",
    "1801500": "Absorventes higiênicos externos",
    "1801600": "Absorventes higiênicos internos (tampões)",
    "1801700": "Papel higiênico — folha simples",
    "1801800": "Papel higiênico — folha dupla",
    "1801900": "Fraldas descartáveis",
    "1802000": "Hastes flexíveis (cotonetes)",
    "1802100": "Aparelhos e lâminas de barbear descartáveis",
    "1802200": "Escovas de dente",

    # ═══ 19 — Eletrônicos/Eletrodomésticos ═══
    "1900100": "Fogões de cozinha de uso doméstico a gás",
    "1900200": "Combinações de refrigeradores e congeladores (geladeiras duplex)",
    "1900300": "Refrigeradores domésticos",
    "1900400": "Congeladores (freezers) domésticos",
    "1900500": "Máquinas de lavar roupa — uso doméstico",
    "1900600": "Máquinas de lavar louça — uso doméstico",
    "1900700": "Máquinas de secar roupa — uso doméstico",
    "1900800": "Aparelhos condicionadores de ar — uso doméstico",
    "1900900": "Aspiradores de pó — uso doméstico",
    "1901000": "Aparelhos eletromecânicos com motor incorporado (liquidificadores, batedeiras, etc.)",
    "1901100": "Telefone celular — smartphone",
    "1901200": "Monitor de vídeo — uso com computadores",
    "1901300": "Receptor de televisão — televisores",
    "1901500": "Aparelhos receptores de radiodifusão",

    # ═══ 20 — Rações para animais ═══
    "2000100": "Rações tipo pet para cães e gatos, acondicionadas em embalagem ≤ 25 kg",
    "2000200": "Rações tipo pet para cães e gatos, acondicionadas em embalagem > 25 kg",
    "2000300": "Outras rações tipo pet (aves, peixes, roedores, etc.)",

    # ═══ 21 — Sorvetes ═══
    "2100100": "Sorvetes de qualquer espécie — inclusive picolés",
    "2100200": "Preparados para fabricação de sorvete em máquina",

    # ═══ 22 — Tintas e Vernizes ═══
    "2200100": "Tintas, vernizes e outras — à base de polímeros acrílicos dispersos em meio aquoso",
    "2200200": "Tintas, vernizes e outras — à base de polímeros acrílicos em meio não aquoso",
    "2200300": "Tintas, vernizes e outras — à base de poliésteres",
    "2200400": "Tintas, vernizes e outras — à base de polímeros sintéticos ou naturais",
    "2200500": "Massas, pastas, ceras, encáusticas e preparações semelhantes para dar brilho",
    "2200600": "Piche (betume) e preparações semelhantes para pintura",
    "2200700": "Solventes e diluentes compostos para vernizes e preparações semelhantes",
    "2200800": "Corantes e pigmentos para preparação de tintas ou vernizes",
}


def is_valid_cest_format(cest: str) -> bool:
    """Verifica se o CEST tem formato válido: 7 dígitos numéricos.

    Aceita com ou sem pontos (ex: '0300700' ou '03.007.00').
    """
    clean = cest.replace(".", "")
    return len(clean) == 7 and clean.isdigit()


def normalize_cest(cest: str) -> str:
    """Remove pontos e espaços do CEST, retornando 7 dígitos."""
    return cest.replace(".", "").replace(" ", "").strip()


def get_cest_descricao(cest: str) -> str | None:
    """Retorna a descrição do CEST ou None se não encontrado na tabela."""
    clean = normalize_cest(cest)
    return CEST_VAREJO.get(clean)


def format_cest(cest: str) -> str:
    """Formata CEST com pontos: SS.GGG.II."""
    clean = normalize_cest(cest)
    if len(clean) != 7:
        return cest
    return f"{clean[:2]}.{clean[2:5]}.{clean[5:7]}"


def get_segmento(cest: str) -> str | None:
    """Retorna a descrição do segmento do CEST."""
    clean = normalize_cest(cest)
    if len(clean) < 2:
        return None
    return SEGMENTOS_CEST.get(clean[:2])


def search_cest(termo: str, limite: int = 10) -> list[tuple[str, str]]:
    """Busca CESTs cuja descrição contenha o termo (case-insensitive).

    Args:
        termo: texto de busca
        limite: máximo de resultados

    Returns:
        Lista de tuplas (cest_code, descricao)
    """
    termo_lower = termo.lower().strip()
    if not termo_lower:
        return []

    resultados: list[tuple[str, str, int]] = []
    for code, desc in CEST_VAREJO.items():
        desc_lower = desc.lower()
        if termo_lower in desc_lower:
            pos = desc_lower.index(termo_lower)
            score = pos + len(desc)
            resultados.append((code, desc, score))

    resultados.sort(key=lambda x: x[2])
    return [(code, desc) for code, desc, _ in resultados[:limite]]
