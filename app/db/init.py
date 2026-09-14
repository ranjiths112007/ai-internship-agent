from __future__ import annotations

import logging
from app.db.session import engine, Base
from app.db.models import JobModel, ApplicationModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_init")


def init_db() -> None:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


if __name__ == "__main__":
    init_db()
