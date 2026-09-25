import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key")


@pytest.fixture
def client():
    from app import app

    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.test_client() as test_client:
        yield test_client