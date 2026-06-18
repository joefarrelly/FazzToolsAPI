import os


def pytest_configure(config):
    """Set required env vars before Django initialises settings."""
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
    os.environ.setdefault("DEBUG_OPTION", "True")
    os.environ.setdefault("DB_NAME", "test_db")
    os.environ.setdefault("DB_USER", "test_user")
    os.environ.setdefault("DB_PASSWORD", "test_pass")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "3306")
    os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
    os.environ.setdefault("HASH_KEY", "test-hash-key-for-pytest")
    os.environ.setdefault("BLIZZ_CLIENT", "test-blizz-client")
    os.environ.setdefault("BLIZZ_SECRET", "test-blizz-secret")
    os.environ.setdefault("BLIZZ_REDIRECT_URI", "http://localhost:3000/redirect/")
