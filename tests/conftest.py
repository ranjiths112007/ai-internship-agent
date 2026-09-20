from __future__ import annotations

import pytest

from app.db.init import init_db


@pytest.fixture(scope="session", autouse=True)
def _initialize_test_database():
    """Ensure database tables exist before any test runs.

    `app/main.py` creates tables inside the FastAPI `lifespan` handler, which
    only fires when `TestClient` is used as a context manager (`with
    TestClient(app) as client: ...`). Several tests instantiate a
    module-level `TestClient(app)` without a `with` block, so lifespan never
    runs and the SQLite tables never get created. This session-scoped,
    autouse fixture guarantees the schema exists up front, independent of
    how each test module constructs its client. `init_db()` is idempotent
    (`Base.metadata.create_all`), so it's safe to call even when the
    database already exists.
    """
    init_db()
