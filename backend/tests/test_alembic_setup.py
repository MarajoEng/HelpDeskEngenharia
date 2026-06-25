from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models import Base


BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_alembic_has_initial_revision() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(config)

    assert script.get_current_head() == "0002"
    assert script.get_revision("0001") is not None
    assert script.get_revision("0002") is not None


def test_alembic_env_exposes_project_metadata(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    env_path = BACKEND_DIR / "alembic" / "env.py"
    spec = spec_from_file_location("helpdesk_alembic_env", env_path)
    assert spec is not None
    assert spec.loader is not None

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.get_database_url() == "sqlite+pysqlite:///:memory:"
    assert module.get_target_metadata() is Base.metadata
    assert "tickets" in module.get_target_metadata().tables
