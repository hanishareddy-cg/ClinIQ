from backend.config import Settings


def test_postgres_url_format():
    s = Settings(
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="testdb",
        postgres_user="user",
        postgres_password="pass",
    )
    assert s.postgres_url == "postgresql+asyncpg://user:pass@localhost:5432/testdb"


def test_postgres_url_sync_format():
    s = Settings(
        postgres_host="myhost",
        postgres_port=5433,
        postgres_db="cliniq",
        postgres_user="admin",
        postgres_password="secret",
    )
    assert s.postgres_url_sync == "postgresql+psycopg2://admin:secret@myhost:5433/cliniq"


def test_defaults():
    s = Settings(postgres_password="x")
    assert s.app_env == "development"
    assert s.es_index == "clinical_notes"
    assert s.es_port == 9200
