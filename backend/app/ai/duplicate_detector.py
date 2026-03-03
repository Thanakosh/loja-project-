"""Detecção de produtos duplicados via similaridade de embeddings.

Gera embeddings vetoriais a partir da descrição do produto e compara
com os existentes no banco para sugerir possíveis duplicatas.

Modelo utilizado: all-MiniLM-L6-v2 (sentence-transformers) — leve (~80MB),
rápido e com boa qualidade para português via multilingual fine-tuning.

Fallback: quando sentence-transformers não está instalado, usa TF-IDF
do scikit-learn como alternativa sem GPU e sem download de modelo.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# ─── Configuração ───

SIMILARITY_THRESHOLD = 0.85  # Acima disso → provável duplicata
SIMILARITY_WARNING = 0.70    # Acima disso → possível duplicata (alerta)
EMBEDDING_DIM = 384          # Dimensão do all-MiniLM-L6-v2
MODEL_NAME = "all-MiniLM-L6-v2"

# ─── Resultado ───


@dataclass(frozen=True)
class DuplicateCandidate:
    """Um produto existente que pode ser duplicata do novo."""

    produto_id: int
    produto_nome: str
    similaridade: float  # 0.0 a 1.0
    nivel: str           # "duplicata" | "alerta" | "ok"


@dataclass
class DuplicateCheckResult:
    """Resultado da verificação de duplicatas."""

    descricao_consultada: str
    candidatos: List[DuplicateCandidate] = field(default_factory=list)
    metodo: str = "embedding"  # "embedding" | "tfidf"

    @property
    def tem_duplicata(self) -> bool:
        return any(c.nivel == "duplicata" for c in self.candidatos)

    @property
    def tem_alerta(self) -> bool:
        return any(c.nivel in ("duplicata", "alerta") for c in self.candidatos)

    def to_dict(self) -> dict:
        return {
            "descricao_consultada": self.descricao_consultada,
            "tem_duplicata": self.tem_duplicata,
            "tem_alerta": self.tem_alerta,
            "metodo": self.metodo,
            "candidatos": [
                {
                    "produto_id": c.produto_id,
                    "produto_nome": c.produto_nome,
                    "similaridade": round(c.similaridade, 4),
                    "nivel": c.nivel,
                }
                for c in self.candidatos
            ],
        }


# ─── Normalização de texto ───


def normalizar_descricao(texto: str) -> str:
    """Normaliza descrição para melhorar qualidade do embedding.

    - Lowercase
    - Remove caracteres especiais desnecessários
    - Normaliza unidades comuns (2L → 2 litros, 500ML → 500 ml)
    - Colapsa espaços múltiplos
    """
    t = texto.lower().strip()

    # Normalizar unidades de medida comuns
    t = re.sub(r"(\d+)\s*ml\b", r"\1 ml", t)
    t = re.sub(r"(\d+)\s*l\b", r"\1 litros", t)
    t = re.sub(r"(\d+)\s*lt\b", r"\1 litros", t)
    t = re.sub(r"(\d+)\s*kg\b", r"\1 kg", t)
    t = re.sub(r"(\d+)\s*g\b", r"\1 g", t)
    t = re.sub(r"(\d+)\s*un\b", r"\1 unidades", t)
    t = re.sub(r"(\d+)\s*pct?\b", r"\1 pacote", t)
    t = re.sub(r"(\d+)\s*cx\b", r"\1 caixa", t)

    # Remover caracteres especiais mas manter acentos
    t = re.sub(r"[^\w\sáàâãéèêíìîóòôõúùûçñ]", " ", t)

    # Colapsar espaços
    t = re.sub(r"\s+", " ", t).strip()

    return t


# ─── Motor de Embeddings ───


class _EmbeddingEngine:
    """Abstração sobre o motor de embeddings (sentence-transformers ou TF-IDF)."""

    def __init__(self) -> None:
        self._model = None
        self._method: str = "none"

    @property
    def method(self) -> str:
        return self._method

    def _load_transformer(self) -> bool:
        """Tenta carregar sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
            self._model = SentenceTransformer(MODEL_NAME)
            self._method = "embedding"
            logger.info("Modelo sentence-transformers '%s' carregado.", MODEL_NAME)
            return True
        except ImportError:
            logger.warning(
                "sentence-transformers não instalado. "
                "Instale com: pip install -r requirements-ai.txt"
            )
            return False
        except Exception as exc:
            logger.warning("Falha ao carregar sentence-transformers: %s", exc)
            return False

    def _load_tfidf(self) -> bool:
        """Fallback: usa TF-IDF do scikit-learn."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-untyped]
            self._model = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 4),
                max_features=EMBEDDING_DIM,
                sublinear_tf=True,
            )
            self._method = "tfidf"
            logger.info("Usando TF-IDF como fallback para embeddings.")
            return True
        except ImportError:
            logger.error("Nem sentence-transformers nem scikit-learn estão instalados.")
            return False

    def ensure_loaded(self) -> None:
        """Carrega o motor na primeira chamada (lazy loading)."""
        if self._model is not None:
            return
        if not self._load_transformer():
            if not self._load_tfidf():
                raise RuntimeError(
                    "Nenhum motor de embeddings disponível. "
                    "Instale sentence-transformers ou scikit-learn."
                )

    def encode(self, textos: List[str]) -> NDArray[np.float32]:
        """Gera embeddings para uma lista de textos.

        Retorna: array shape (n, dim) com vetores normalizados (norma L2 = 1).
        """
        self.ensure_loaded()

        if self._method == "embedding":
            vectors = self._model.encode(  # type: ignore[union-attr]
                textos,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return np.asarray(vectors, dtype=np.float32)

        # TF-IDF path
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-untyped]

        assert isinstance(self._model, TfidfVectorizer)

        # Se o vectorizer ainda não foi fitado, fitar com os textos recebidos
        if not hasattr(self._model, "vocabulary_") or not self._model.vocabulary_:
            matrix = self._model.fit_transform(textos)
        else:
            matrix = self._model.transform(textos)

        vectors = matrix.toarray().astype(np.float32)

        # Normalizar para norma L2 = 1 (similaridade cosseno via dot product)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        vectors = vectors / norms

        # Pad ou truncate para EMBEDDING_DIM
        if vectors.shape[1] < EMBEDDING_DIM:
            pad = np.zeros((vectors.shape[0], EMBEDDING_DIM - vectors.shape[1]), dtype=np.float32)
            vectors = np.hstack([vectors, pad])
        elif vectors.shape[1] > EMBEDDING_DIM:
            vectors = vectors[:, :EMBEDDING_DIM]

        return vectors

    def encode_single(self, texto: str) -> NDArray[np.float32]:
        """Gera embedding para um único texto. Retorna vetor shape (dim,)."""
        return self.encode([texto])[0]


# Singleton global (lazy loaded)
_engine = _EmbeddingEngine()


def get_engine() -> _EmbeddingEngine:
    """Retorna a instância singleton do motor de embeddings."""
    return _engine


# ─── Serialização de embeddings para o banco ───


def embedding_to_json(vector: NDArray[np.float32]) -> str:
    """Serializa um vetor numpy para string JSON (armazenamento no banco)."""
    return json.dumps(vector.tolist())


def embedding_from_json(json_str: str) -> NDArray[np.float32]:
    """Deserializa uma string JSON para vetor numpy."""
    return np.array(json.loads(json_str), dtype=np.float32)


# ─── Similaridade ───


def cosine_similarity_batch(
    query: NDArray[np.float32],
    candidates: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calcula similaridade cosseno entre query e N candidatos.

    Assume vetores já normalizados (norma L2 = 1), então basta dot product.

    Args:
        query: vetor shape (dim,)
        candidates: matriz shape (n, dim)

    Returns:
        array shape (n,) com similaridades [-1, 1]
    """
    if candidates.ndim == 1:
        candidates = candidates.reshape(1, -1)
    return candidates @ query


def classificar_nivel(similaridade: float) -> str:
    """Classifica o nível de similaridade."""
    if similaridade >= SIMILARITY_THRESHOLD:
        return "duplicata"
    if similaridade >= SIMILARITY_WARNING:
        return "alerta"
    return "ok"


# ─── Função principal ───


def verificar_duplicatas(
    descricao_nova: str,
    produtos_existentes: Sequence[tuple[int, str, Optional[str]]],
    limite_resultados: int = 5,
) -> DuplicateCheckResult:
    """Verifica se uma descrição de produto é similar a produtos já cadastrados.

    Args:
        descricao_nova: descrição do produto a ser verificado
        produtos_existentes: lista de (id, nome, embedding_json | None)
            Se embedding_json for None, gera embedding on-the-fly
        limite_resultados: máximo de candidatos a retornar

    Returns:
        DuplicateCheckResult com os candidatos ordenados por similaridade
    """
    engine = get_engine()

    desc_normalizada = normalizar_descricao(descricao_nova)
    query_vec = engine.encode_single(desc_normalizada)

    # Separar produtos com e sem embedding salvo
    ids: List[int] = []
    nomes: List[str] = []
    embeddings: List[NDArray[np.float32]] = []

    sem_embedding: List[tuple[int, str]] = []

    for prod_id, prod_nome, emb_json in produtos_existentes:
        if emb_json:
            ids.append(prod_id)
            nomes.append(prod_nome)
            embeddings.append(embedding_from_json(emb_json))
        else:
            sem_embedding.append((prod_id, prod_nome))

    # Gerar embeddings para produtos que não têm
    if sem_embedding:
        textos = [normalizar_descricao(nome) for _, nome in sem_embedding]
        novos_vecs = engine.encode(textos)
        for i, (prod_id, prod_nome) in enumerate(sem_embedding):
            ids.append(prod_id)
            nomes.append(prod_nome)
            embeddings.append(novos_vecs[i])

    if not embeddings:
        return DuplicateCheckResult(
            descricao_consultada=descricao_nova,
            metodo=engine.method,
        )

    # Calcular similaridades
    candidates_matrix = np.stack(embeddings)
    sims = cosine_similarity_batch(query_vec, candidates_matrix)

    # Montar candidatos ordenados por similaridade (desc)
    indexed = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)

    candidatos: List[DuplicateCandidate] = []
    for idx, sim_score in indexed[:limite_resultados]:
        sim_float = float(sim_score)
        nivel = classificar_nivel(sim_float)
        if nivel == "ok":
            break  # Os próximos serão ainda menores
        candidatos.append(DuplicateCandidate(
            produto_id=ids[idx],
            produto_nome=nomes[idx],
            similaridade=sim_float,
            nivel=nivel,
        ))

    return DuplicateCheckResult(
        descricao_consultada=descricao_nova,
        candidatos=candidatos,
        metodo=engine.method,
    )


def gerar_embedding_produto(descricao: str) -> str:
    """Gera embedding de uma descrição e retorna como JSON (para salvar no banco).

    Uso típico: ao criar/atualizar produto, salvar o embedding no campo `embedding`.
    """
    engine = get_engine()
    desc_norm = normalizar_descricao(descricao)
    vec = engine.encode_single(desc_norm)
    return embedding_to_json(vec)
