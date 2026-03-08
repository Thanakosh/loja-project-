"""Tabela NCM — Nomenclatura Comum do MERCOSUL (subconjunto varejo).

Fonte: TEC/MDIC — Tarifa Externa Comum.
A tabela completa possui ~13.000 códigos. Aqui estão os ~250 NCMs
mais comuns no varejo brasileiro para validação e sugestão.

Formato: 8 dígitos numéricos (XXXX.XX.XX), armazenados sem pontos.
"""

from __future__ import annotations

import re
from typing import List, Tuple

# NCM: código (8 dígitos sem pontos) → descrição
NCM_VAREJO: dict[str, str] = {
    # ══ Alimentos e Bebidas ══
    "02011000": "Carnes de bovino, frescas ou refrigeradas — carcaças e meias-carcaças",
    "02012090": "Carnes de bovino, frescas ou refrigeradas — outras peças não desossadas",
    "02013000": "Carnes de bovino desossadas, frescas ou refrigeradas",
    "02021000": "Carnes de bovino, congeladas — carcaças e meias-carcaças",
    "02023000": "Carnes de bovino desossadas, congeladas",
    "02031100": "Carnes de suíno, frescas ou refrigeradas — carcaças e meias-carcaças",
    "02032900": "Carnes de suíno congeladas — outras",
    "02071100": "Carnes de aves (galos/galinhas) — não cortadas em pedaços, frescas ou refrigeradas",
    "02071200": "Carnes de aves (galos/galinhas) — não cortadas em pedaços, congeladas",
    "02071400": "Carnes de aves — pedaços e miudezas, congelados",
    "03021900": "Peixes frescos ou refrigerados — outros salmonídeos",
    "03034900": "Peixes congelados — atuns, outros",
    "04011000": "Leite e creme de leite, não concentrados — teor de gordura ≤ 1%",
    "04012000": "Leite e creme de leite, não concentrados — teor de gordura 1% a 6%",
    "04014000": "Leite e creme de leite, não concentrados — teor de gordura > 10%",
    "04021000": "Leite em pó ou grânulos — teor de gordura ≤ 1,5%",
    "04022100": "Leite em pó ou grânulos — teor de gordura > 1,5%, sem açúcar",
    "04031000": "Iogurte",
    "04041000": "Soro de leite",
    "04051000": "Manteiga",
    "04061000": "Queijos frescos (incluindo de soro) e requeijão",
    "04063000": "Queijos fundidos",
    "04069000": "Outros queijos",
    "04070090": "Ovos de galinha — outros",
    "04090000": "Mel natural",
    "07019000": "Batatas frescas ou refrigeradas — outras",
    "07020000": "Tomates frescos ou refrigerados",
    "07031019": "Cebolas frescas ou refrigeradas",
    "07041000": "Couve-flor e brócolos — frescos ou refrigerados",
    "07049000": "Couves e outros — frescos ou refrigerados",
    "07051100": "Alface — fresca ou refrigerada",
    "07061000": "Cenouras e nabos — frescos ou refrigerados",
    "07093000": "Berinjelas frescas ou refrigeradas",
    "07096010": "Pimentões — frescos ou refrigerados",
    "07099100": "Alcachofras — frescas ou refrigeradas",
    "08030000": "Bananas frescas ou secas",
    "08051000": "Laranjas frescas ou secas",
    "08052000": "Tangerinas e similares",
    "08061000": "Uvas frescas",
    "08071100": "Melancias frescas",
    "08071900": "Melões frescos — outros",
    "08081000": "Maçãs frescas",
    "08109040": "Mangas frescas",
    "09011100": "Café não torrado, não descafeinado",
    "09012100": "Café torrado, não descafeinado",
    "09012200": "Café torrado, descafeinado",
    "09021000": "Chá verde (não fermentado)",
    "09024000": "Chá preto (fermentado) e chá parcialmente fermentado",
    "10011900": "Trigo e mistura de trigo com centeio — outros",
    "10019900": "Outros trigos",
    "10030090": "Cevada — outros",
    "10051000": "Milho para semeadura",
    "10059010": "Milho em grão — para pipoca",
    "10059090": "Milho em grão — outros",
    "10061011": "Arroz com casca — para semeadura",
    "10063011": "Arroz semibranqueado ou branqueado, polido ou não — parboilizado",
    "10063021": "Arroz semibranqueado ou branqueado, polido ou não — não parboilizado",
    "11010010": "Farinha de trigo",
    "11022000": "Farinha de milho",
    "11031300": "Grumos e sêmolas de milho",
    "11041900": "Grãos trabalhados — outros cereais",
    "12010090": "Soja — para semeadura, outros",
    "12019000": "Soja, mesmo triturada — outros",
    "15071000": "Óleo de soja, bruto",
    "15079011": "Óleo de soja, refinado — em recipientes ≤ 5L",
    "15079019": "Óleo de soja, refinado — outros",
    "15091000": "Azeite de oliva, virgem",
    "15099000": "Azeite de oliva — outros",
    "15141100": "Óleo de canola e colza, brutos — baixo teor de ácido erúcico",
    "15141900": "Óleo de canola e colza, brutos — outros",
    "15171000": "Margarina (exceto líquida)",
    "16010000": "Enchidos e produtos semelhantes de carne",
    "16023200": "Preparações e conservas de aves (galos, galinhas, etc.)",
    "17011400": "Outros açúcares de cana",
    "17019900": "Outros açúcares — sacarose quimicamente pura",
    "17023000": "Glicose quimicamente pura (dextrose)",
    "17049020": "Chocolates e preparações alimentícias contendo cacau",
    "17049090": "Outros produtos de confeitaria sem cacau",
    "18063100": "Chocolate em tabletes ou barras, recheado",
    "18063200": "Chocolate em tabletes ou barras, não recheado",
    "18069000": "Outros chocolates e preparações contendo cacau",
    "19019090": "Outras preparações alimentícias de farinhas, amidos ou féculas",
    "19021100": "Massas alimentícias não cozidas, não recheadas — contendo ovos",
    "19021900": "Massas alimentícias não cozidas, não recheadas — outras",
    "19023000": "Massas alimentícias — outras",
    "19041000": "Produtos à base de cereais obtidos por expansão ou torrefação",
    "19053100": "Biscoitos adicionados de adoçante",
    "19053200": "Waffles e wafers",
    "19054000": "Torradas, pão torrado e produtos semelhantes torrados",
    "19059090": "Outros produtos de padaria ou pastelaria",
    "20019000": "Outros produtos hortícolas, frutas e outras partes comestíveis, preparados com vinagre",
    "20021000": "Tomates inteiros ou em pedaços, preparados ou conservados",
    "20029090": "Tomates preparados ou conservados — outros",
    "20079910": "Geleias e marmelades",
    "20079990": "Outras preparações de frutas",
    "20081900": "Outras frutas de casca rija, preparadas ou conservadas",
    "20089900": "Outras frutas e partes de plantas, preparadas ou conservadas",
    "20091100": "Sumo de laranja, congelado",
    "20091900": "Sumo de laranja — outros",
    "20098900": "Sucos de outras frutas — outros",
    "20099000": "Misturas de sucos",
    "21011100": "Extratos, essências e concentrados de café",
    "21012000": "Extratos, essências e concentrados de chá ou mate",
    "21031000": "Molho de soja",
    "21032010": "Ketchup e outros molhos de tomate",
    "21032090": "Outros molhos e preparações para molhos",
    "21033010": "Mostarda preparada",
    "21033021": "Mostarda em pó",
    "21039011": "Maionese",
    "21039019": "Outros condimentos e temperos compostos",
    "21039090": "Outros molhos e condimentos",
    "21050000": "Sorvetes",
    "21069010": "Preparações compostas não alcoólicas para elaboração de bebidas",
    "21069090": "Preparações alimentícias não especificadas",

    # ══ Bebidas ══
    "22011000": "Águas minerais e gasosas naturais",
    "22019000": "Outras águas — gelo e neve",
    "22021000": "Águas com adição de açúcar ou aromatizadas",
    "22029000": "Outras bebidas não alcoólicas (exceto sucos)",
    "22030000": "Cerveja de malte",
    "22041000": "Vinhos espumantes e espumosos",
    "22042100": "Vinhos em recipientes ≤ 2L",
    "22042900": "Vinhos em recipientes > 2L",
    "22059000": "Outros vermutes e vinhos aromatizados",
    "22060000": "Outras bebidas fermentadas (sidra, perada, hidromel)",
    "22071000": "Álcool etílico não desnaturado ≥ 80%",
    "22082000": "Aguardentes de vinho ou de bagaço de uvas",
    "22084000": "Rum e outras aguardentes de cana",
    "22085000": "Gin e genebra",
    "22086000": "Vodca",
    "22087000": "Licores",
    "22089000": "Outras bebidas alcoólicas destiladas",

    # ══ Higiene e Limpeza ══
    "33030000": "Perfumes e águas-de-colônia",
    "33041000": "Produtos de maquiagem para os lábios",
    "33042000": "Produtos de maquiagem para os olhos",
    "33043000": "Preparações para manicuros e pedicuros",
    "33049100": "Pós para maquiagem (incluindo talcos)",
    "33049900": "Outros produtos de beleza ou de maquiagem",
    "33051000": "Xampus",
    "33052000": "Preparações para ondulação ou alisamento permanentes",
    "33053000": "Laquê para o cabelo",
    "33059000": "Outras preparações capilares",
    "33061000": "Dentifrícios (cremes dentais)",
    "33069000": "Outras preparações para higiene bucal",
    "33071000": "Preparações para barbear",
    "33072000": "Desodorantes corporais e antiperspirantes",
    "33073000": "Sais perfumados para banho",
    "33079000": "Outras preparações de perfumaria ou cosmética",
    "34011100": "Sabões de toucador",
    "34011900": "Outros sabões em barra",
    "34012000": "Sabões — outros",
    "34022000": "Preparações para lavagem — acondicionadas para venda a retalho",
    "34029000": "Outras preparações para lavagem e limpeza",
    "34031100": "Preparações para tratamento de têxteis ou couros contendo ≥ 70% de óleos de petróleo",
    "34039100": "Outras preparações lubrificantes contendo ≥ 70% de óleos de petróleo",
    "34051000": "Pomadas, cremes e preparações semelhantes para calçados",
    "34054000": "Pastas, pós e outras preparações para arear",
    "34059000": "Outras preparações para limpeza e polimento",
    "38089190": "Inseticidas — outros",
    "38089290": "Fungicidas — outros",
    "38089990": "Outros desinfetantes, raticidas e semelhantes",

    # ══ Papel e Descartáveis ══
    "48030000": "Papel higiênico e semelhantes (papel tissue)",
    "48181000": "Papel higiênico",
    "48182000": "Lenços, incluindo de desmaquiar, de papel",
    "48183000": "Toalhas de mão de papel",
    "48184000": "Absorventes e tampões higiênicos, fraldas",
    "48189000": "Artigos semelhantes para usos domésticos de papel",

    # ══ Vestuário ══
    "61033900": "Paletós e blazers de malha — outras matérias têxteis",
    "61034300": "Calças de malha — fibras sintéticas",
    "61042300": "Conjuntos de malha para mulheres — fibras sintéticas",
    "61043300": "Paletós e blazers de malha para mulheres — fibras sintéticas",
    "61046300": "Calças de malha para mulheres — fibras sintéticas",
    "61051000": "Camisas de malha para homens — algodão",
    "61052000": "Camisas de malha para homens — fibras sintéticas ou artificiais",
    "61061000": "Camisas e blusas de malha para mulheres — algodão",
    "61062000": "Camisas e blusas de malha para mulheres — fibras sintéticas",
    "61091000": "Camisetas (T-shirts) de malha — algodão",
    "61099000": "Camisetas (T-shirts) de malha — outras matérias têxteis",
    "61101100": "Suéteres (pulôveres) de malha — lã",
    "61102000": "Suéteres (pulôveres) de malha — algodão",
    "61103000": "Suéteres (pulôveres) de malha — fibras sintéticas ou artificiais",
    "61112000": "Vestuário para bebês de malha — algodão",
    "61112090": "Vestuário para bebês de malha — outros",
    "61159900": "Meias-calças e semelhantes de malha — outras matérias têxteis",
    "62034200": "Calças de algodão (não de malha)",
    "62034300": "Calças de fibras sintéticas (não de malha)",
    "62046200": "Calças de algodão para mulheres (não de malha)",
    "62046300": "Calças de fibras sintéticas para mulheres (não de malha)",
    "64019200": "Calçados impermeáveis cobrindo o tornozelo — borracha/plástico",
    "64021200": "Calçados para esqui e snowboard",
    "64021900": "Calçados para esportes — outros",
    "64029900": "Outros calçados com sola e parte superior de borracha ou plástico",
    "64039100": "Calçados com sola de borracha/plástico e parte superior de couro — cobrindo o tornozelo",
    "64039900": "Calçados com sola de borracha/plástico e parte superior de couro — outros",
    "64041100": "Calçados para esportes com sola de borracha/plástico e parte superior de têxteis",
    "64041900": "Outros calçados com sola de borracha/plástico e parte superior de têxteis",
    "64052000": "Calçados com parte superior de matérias têxteis — outros",

    # ══ Eletrônicos e Informática ══
    "84713012": "Computadores portáteis (laptops) — peso ≤ 3,5 kg",
    "84713019": "Computadores portáteis (laptops) — outros",
    "84714900": "Outras máquinas automáticas para processamento de dados",
    "84716052": "Mouses e trackballs",
    "84716053": "Teclados",
    "84716060": "Scanners",
    "84717012": "Discos rígidos (HD/SSD)",
    "84717019": "Outras unidades de memória",
    "84718000": "Outras unidades de máquinas automáticas para processamento de dados",
    "84719000": "Outras máquinas automáticas para processamento de dados e suas unidades — partes",
    "85171200": "Telefones celulares e para redes sem fio",
    "85176200": "Aparelhos para recepção, conversão e transmissão de dados — roteadores",
    "85176299": "Aparelhos para redes sem fio — outros",
    "85184000": "Amplificadores elétricos de audiofrequência",
    "85198100": "Aparelhos de reprodução de som que funcionam sem gravação",
    "85219000": "Aparelhos de gravação ou reprodução de vídeo — outros",
    "85258000": "Câmeras de televisão, câmeras fotográficas digitais e câmeras de vídeo",
    "85285100": "Monitores com tubo de raios catódicos",
    "85285200": "Monitores — outros (LCD, LED, OLED)",
    "85286100": "Projetores — com tubo de raios catódicos",
    "85286200": "Projetores — outros (LCD, DLP)",
    "85287100": "Receptores de televisão — sem monitor",
    "85287200": "Receptores de televisão — a cores",
    "85340000": "Circuitos impressos",

    # ══ Eletrodomésticos ══
    "84501100": "Máquinas de lavar roupa — totalmente automáticas, cap. ≤ 10 kg",
    "84501200": "Máquinas de lavar roupa — com centrifugador incorporado, cap. ≤ 10 kg",
    "84502000": "Máquinas de lavar roupa — capacidade > 10 kg",
    "84181000": "Combinações de refrigeradores e congeladores com portas exteriores separadas",
    "84182100": "Refrigeradores domésticos — compressão",
    "84183000": "Congeladores (freezers) horizontais, cap. ≤ 800L",
    "84184000": "Congeladores (freezers) verticais, cap. ≤ 900L",
    "84221100": "Máquinas de lavar louça — domésticas",
    "84501900": "Máquinas de lavar roupa — outras",
    "85161000": "Aquecedores elétricos de água instantâneos ou de acumulação e aquecedores de imersão",
    "85162100": "Radiadores de acumulação elétricos para aquecimento de ambientes",
    "85163200": "Aparelhos elétricos para arranjos do cabelo — outros",
    "85165000": "Fornos de micro-ondas",
    "85166000": "Outros fornos elétricos, fogões, fogareiros, grelhas e assadeiras",
    "85167100": "Aparelhos eletrotérmicos para preparação de café ou chá",
    "85167200": "Torradeiras elétricas",
    "85167900": "Outros aparelhos eletrotérmicos — uso doméstico",

    # ══ Combustíveis ══
    "27101259": "Gasolina automotiva — outras",
    "27101921": "Óleo diesel — outros",
    "27111300": "Gás liquefeito de petróleo (GLP) — butanos",
    "27112100": "Gás natural — no estado gasoso",
    "22071000": "Álcool etílico (etanol) não desnaturado ≥ 80%",

    # ══ Materiais de Construção ══
    "68022100": "Mármore e travertinos — trabalhados",
    "68022300": "Granito — trabalhado",
    "69072100": "Ladrilhos e placas de cerâmica — coeficiente de absorção ≤ 0,5%",
    "69072300": "Ladrilhos e placas de cerâmica — coeficiente de absorção > 10%",
    "69089000": "Outros ladrilhos e placas de cerâmica",
    "70052100": "Vidro flotado — incolor, em chapas",
    "70052900": "Vidro flotado — corado ou opacificado",
    "72142000": "Barras de ferro ou aço — com nervuras",
    "73066100": "Tubos de ferro ou aço — soldados, de seção quadrada ou retangular",
    "73083000": "Portas, janelas e respectivos caixilhos, de ferro ou aço",

    # ══ Automotivo (peças e acessórios) ══
    "40111000": "Pneumáticos novos — de borracha, para automóveis de passageiros",
    "40112000": "Pneumáticos novos — de borracha, para ônibus e caminhões",
    "40119200": "Pneumáticos novos — outros, de construção radial",
    "87089990": "Outras partes e acessórios para veículos automóveis",
}


def is_valid_ncm_format(ncm: str) -> bool:
    """Verifica se o NCM tem formato válido: 8 dígitos numéricos.

    Aceita com ou sem pontos (ex: '61091000' ou '6109.10.00').
    """
    clean = ncm.replace(".", "")
    return len(clean) == 8 and clean.isdigit()


def normalize_ncm(ncm: str) -> str:
    """Remove pontos e espaços do NCM, retornando 8 dígitos."""
    return ncm.replace(".", "").replace(" ", "").strip()


def get_ncm_descricao(ncm: str) -> str | None:
    """Retorna a descrição do NCM ou None se não encontrado na tabela."""
    clean = normalize_ncm(ncm)
    return NCM_VAREJO.get(clean)


def format_ncm(ncm: str) -> str:
    """Formata NCM com pontos: XXXX.XX.XX."""
    clean = normalize_ncm(ncm)
    if len(clean) != 8:
        return ncm
    return f"{clean[:4]}.{clean[4:6]}.{clean[6:8]}"


def search_ncm(termo: str, limite: int = 10) -> List[Tuple[str, str]]:
    """Busca NCMs cuja descrição contenha o termo (case-insensitive).

    Args:
        termo: texto de busca (ex: "café", "camiseta", "refrigerador")
        limite: máximo de resultados

    Returns:
        Lista de tuplas (ncm_code, descricao) ordenada por relevância
    """
    termo_lower = termo.lower().strip()
    if not termo_lower:
        return []

    # Busca simples por substring
    resultados: list[tuple[str, str, int]] = []
    for code, desc in NCM_VAREJO.items():
        desc_lower = desc.lower()
        if termo_lower in desc_lower:
            # Score: mais curta a descrição e mais próximo do início, maior relevância
            pos = desc_lower.index(termo_lower)
            score = pos + len(desc)
            resultados.append((code, desc, score))

    # Ordenar por score (menor = mais relevante)
    resultados.sort(key=lambda x: x[2])
    return [(code, desc) for code, desc, _ in resultados[:limite]]
