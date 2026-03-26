"""Testes para detecção de duplicatas (duplicate_detector.py + endpoint)."""

from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from app.ai.duplicate_detector import (
    normalizar_descricao,
    cosine_similarity_batch,
    classificar_nivel,
    embedding_to_json,
    embedding_from_json,
    DuplicateCandidate,
    DuplicateCheckResult,
    SIMILARITY_THRESHOLD,
    SIMILARITY_WARNING,
    verificar_duplicatas,
)


# ─── Normalização de texto ───


class TestNormalizarDescricao:
    def test_lowercase(self):
        assert normalizar_descricao("COCA COLA") == "coca cola"

    def test_normaliza_litros(self):
        result = normalizar_descricao("Coca Cola 2L")
        assert "2 litros" in result

    def test_normaliza_ml(self):
        result = normalizar_descricao("Guaraná 350ML")
        assert "350 ml" in result

    def test_normaliza_kg(self):
        result = normalizar_descricao("Arroz 5KG")
        assert "5 kg" in result

    def test_normaliza_unidades(self):
        result = normalizar_descricao("Papel 500UN")
        assert "500 unidades" in result

    def test_remove_chars_especiais(self):
        result = normalizar_descricao("Coca-Cola® 2L (PET)")
        # Hífens e símbolos removidos, mas conteúdo preservado
        assert "coca" in result
        assert "cola" in result
        assert "2 litros" in result

    def test_colapsa_espacos(self):
        result = normalizar_descricao("  Coca   Cola   2L  ")
        assert "  " not in result
        assert result == normalizar_descricao("Coca Cola 2L")

    def test_preserva_acentos(self):
        result = normalizar_descricao("Café Torrado Moído")
        assert "café" in result
        assert "moído" in result


# ─── Serialização de embeddings ───


class TestEmbeddingSerialization:
    def test_roundtrip(self):
        vec = np.array([0.1, 0.2, 0.3, -0.5], dtype=np.float32)
        json_str = embedding_to_json(vec)
        recovered = embedding_from_json(json_str)
        np.testing.assert_array_almost_equal(vec, recovered)

    def test_json_format(self):
        vec = np.array([1.0, 2.0], dtype=np.float32)
        json_str = embedding_to_json(vec)
        assert json_str == "[1.0, 2.0]"


# ─── Similaridade cosseno ───


class TestCosineSimilarity:
    def test_identico(self):
        vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        sim = cosine_similarity_batch(vec, vec.reshape(1, -1))
        assert abs(sim[0] - 1.0) < 0.001

    def test_ortogonal(self):
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        sim = cosine_similarity_batch(v1, v2.reshape(1, -1))
        assert abs(sim[0]) < 0.001

    def test_oposto(self):
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = np.array([-1.0, 0.0], dtype=np.float32)
        sim = cosine_similarity_batch(v1, v2.reshape(1, -1))
        assert sim[0] < -0.99

    def test_batch(self):
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        candidates = np.array([
            [1.0, 0.0, 0.0],  # identico
            [0.0, 1.0, 0.0],  # ortogonal
            [0.7071, 0.7071, 0.0],  # 45 graus
        ], dtype=np.float32)
        sims = cosine_similarity_batch(query, candidates)
        assert len(sims) == 3
        assert sims[0] > 0.99   # identico
        assert abs(sims[1]) < 0.01  # ortogonal
        assert 0.6 < sims[2] < 0.8  # ~0.707


# ─── Classificação de nível ───


class TestClassificarNivel:
    def test_duplicata(self):
        assert classificar_nivel(0.90) == "duplicata"
        assert classificar_nivel(SIMILARITY_THRESHOLD) == "duplicata"

    def test_alerta(self):
        assert classificar_nivel(0.75) == "alerta"
        assert classificar_nivel(SIMILARITY_WARNING) == "alerta"

    def test_ok(self):
        assert classificar_nivel(0.50) == "ok"
        assert classificar_nivel(0.0) == "ok"


# ─── Dataclasses resultado ───


class TestDuplicateCheckResult:
    def test_sem_candidatos(self):
        result = DuplicateCheckResult(descricao_consultada="teste")
        assert not result.tem_duplicata
        assert not result.tem_alerta
        d = result.to_dict()
        assert d["tem_duplicata"] is False
        assert d["candidatos"] == []

    def test_com_duplicata(self):
        result = DuplicateCheckResult(
            descricao_consultada="Coca Cola 2L",
            candidatos=[
                DuplicateCandidate(
                    produto_id=1,
                    produto_nome="COCA COLA 2L PET",
                    similaridade=0.92,
                    nivel="duplicata",
                )
            ],
        )
        assert result.tem_duplicata
        assert result.tem_alerta

    def test_com_alerta_sem_duplicata(self):
        result = DuplicateCheckResult(
            descricao_consultada="Coca Cola 2L",
            candidatos=[
                DuplicateCandidate(
                    produto_id=1,
                    produto_nome="Coca Cola 1L",
                    similaridade=0.78,
                    nivel="alerta",
                )
            ],
        )
        assert not result.tem_duplicata
        assert result.tem_alerta

    def test_to_dict_completo(self):
        result = DuplicateCheckResult(
            descricao_consultada="Teste",
            candidatos=[
                DuplicateCandidate(
                    produto_id=42,
                    produto_nome="Produto X",
                    similaridade=0.8765,
                    nivel="alerta",
                )
            ],
            metodo="tfidf",
        )
        d = result.to_dict()
        assert d["metodo"] == "tfidf"
        assert d["candidatos"][0]["similaridade"] == 0.8765
        assert d["candidatos"][0]["produto_id"] == 42


class TestVerificarDuplicatasTFIDF:
    def test_fallback_tfidf_recalcula_query_e_candidatos_no_mesmo_lote(self, monkeypatch):
        import app.ai.duplicate_detector as detector

        class FakeEngine:
            method = "tfidf"

            def ensure_loaded(self):
                return None

            def encode_single(self, texto):
                raise AssertionError("encode_single não deve ser usado no fallback TF-IDF")

            def encode(self, textos):
                assert textos == [
                    "coca cola 2 litros",
                    "coca cola 2 litros pet",
                    "sabao em po 1 kg",
                ]
                return np.array(
                    [
                        [1.0, 0.0, 0.0],
                        [0.95, 0.0, 0.0],
                        [0.2, 0.0, 0.0],
                    ],
                    dtype=np.float32,
                )

        monkeypatch.setattr(detector, "get_engine", lambda: FakeEngine())

        result = verificar_duplicatas(
            descricao_nova="Coca Cola 2L",
            produtos_existentes=[
                (1, "Coca Cola 2L PET", "nao-e-json"),
                (2, "Sabao em po 1kg", "tambem-invalido"),
            ],
            limite_resultados=5,
        )

        assert result.metodo == "tfidf"
        assert result.tem_duplicata is True
        assert len(result.candidatos) == 1
        assert result.candidatos[0].produto_id == 1
        assert result.candidatos[0].nivel == "duplicata"


# ─── Endpoint (integração com TestClient) ───


class TestCheckDuplicateEndpoint:
    """Testes de integração do endpoint /api/v1/ai/check-duplicate."""

    def _get_client_and_headers(self):
        """Helper para importar client e auth_headers do conftest."""
        from app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_sem_auth_retorna_401(self, client):
        """Endpoint protegido deve exigir autenticação."""
        resp = client.post(
            "/api/v1/ai/check-duplicate",
            json={"descricao": "Coca Cola 2L"},
        )
        assert resp.status_code == 401

    def test_payload_invalido_retorna_422(self, client, auth_headers):
        """Descrição vazia deve retornar 422."""
        resp = client.post(
            "/api/v1/ai/check-duplicate",
            json={"descricao": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_check_duplicate_barcode_exato(self, client, auth_headers, db_session):
        """Se código de barras encontrado, retorna match exato."""
        from app.models.produto import Produto

        # Criar produto com barcode
        produto = Produto(
            nome="Coca Cola 2L PET",
            fornecedor="Coca-Cola",
            preco_unitario=8.99,
            preco_liquido=8.99,
            codigo_barras="7894900011517",
            unidade_medida="UN",
        )
        db_session.add(produto)
        db_session.commit()
        db_session.refresh(produto)

        resp = client.post(
            "/api/v1/ai/check-duplicate",
            json={
                "descricao": "Refrigerante Coca-Cola 2 Litros",
                "codigo_barras": "7894900011517",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tem_duplicata"] is True
        assert data["metodo"] == "barcode_exato"
        assert data["candidatos"][0]["produto_id"] == produto.id
        assert data["candidatos"][0]["similaridade"] == 1.0

    def test_check_duplicate_nome_exato(self, client, auth_headers, db_session):
        """Nome identico deve retornar duplicata exata sem depender do motor fuzzy."""
        from app.models.produto import Produto

        produto = Produto(
            nome="POSTE BALIZADOR QDR 30CM C/ VIDRO PT - JRC",
            fornecedor="Fornecedor Teste",
            preco_unitario=120.0,
            preco_liquido=120.0,
            unidade_medida="UN",
        )
        db_session.add(produto)
        db_session.commit()
        db_session.refresh(produto)

        resp = client.post(
            "/api/v1/ai/check-duplicate",
            json={"descricao": "  poste balizador qdr 30cm c/ vidro pt - jrc  "},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tem_duplicata"] is True
        assert data["metodo"] == "nome_exato"
        assert data["candidatos"][0]["produto_id"] == produto.id
        assert data["candidatos"][0]["similaridade"] == 1.0

    def test_check_duplicate_sem_produtos(self, client, auth_headers):
        """Sem produtos no banco, retorna lista vazia sem erro."""
        resp = client.post(
            "/api/v1/ai/check-duplicate",
            json={"descricao": "Produto Novo Inexistente XYZ"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 503)  # 503 se deps AI não instaladas
        if resp.status_code == 200:
            data = resp.json()
            assert data["candidatos"] == []

    def test_check_duplicate_retorna_503_quando_motor_nao_esta_disponivel(self, client, auth_headers, monkeypatch):
        import app.ai.duplicate_detector as detector

        class BrokenEngine:
            def ensure_loaded(self):
                raise RuntimeError("Nenhum motor disponível")

        monkeypatch.setattr(detector, "get_engine", lambda: BrokenEngine())

        resp = client.post(
            "/api/v1/ai/check-duplicate",
            json={"descricao": "Coca Cola 2L"},
            headers=auth_headers,
        )

        assert resp.status_code == 503
        data = resp.json()
        assert "requirements-ai.txt" in data["message"]
        assert "requirements-ai.txt" in data["details"]

    def test_generate_embeddings_sem_auth_retorna_401(self, client):
        resp = client.post("/api/v1/ai/generate-embeddings", json={})
        assert resp.status_code == 401
