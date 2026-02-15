import pytest
from datetime import datetime, timedelta, timezone


def test_oauth_optional_uses_auto_error_false():
    from app.core.security import oauth2_scheme_optional

    assert oauth2_scheme_optional.auto_error is False


def test_async_infrastructure_is_available():
    from app.core import database

    assert hasattr(database, "get_async_engine")
    assert hasattr(database, "get_async_db")


def test_ocr_task_cleanup_and_hash():
    from app.api.v1 import ocr

    ocr.ocr_tasks.clear()
    ocr.ocr_task_index_by_hash.clear()

    file_hash = ocr._build_file_hash(b"same-content")
    task_id = "task-expired"
    ocr.ocr_tasks[task_id] = {
        "status": "completed",
        "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "hash": file_hash,
    }
    ocr.ocr_task_index_by_hash[file_hash] = task_id

    ocr._cleanup_expired_tasks()

    assert task_id not in ocr.ocr_tasks
    assert file_hash not in ocr.ocr_task_index_by_hash


def test_ocr_hash_is_deterministic():
    from app.api.v1 import ocr

    assert ocr._build_file_hash(b"abc") == ocr._build_file_hash(b"abc")
    assert ocr._build_file_hash(b"abc") != ocr._build_file_hash(b"xyz")


def test_ocr_dependency_validation(monkeypatch):
    from app.api.v1 import ocr

    monkeypatch.setattr(ocr.importlib.util, "find_spec", lambda _: None)

    with pytest.raises(Exception) as exc_info:
        ocr._ensure_ocr_dependencies()

    assert "Dependências de OCR não instaladas" in exc_info.value.detail
