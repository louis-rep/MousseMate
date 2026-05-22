from __future__ import annotations

import os
import unittest

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base

load_dotenv()


class BaseTestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        url = os.environ["TEST_DATABASE_URL"]
        cls.engine = create_engine(url)
        Base.metadata.create_all(cls.engine)

    def setUp(self) -> None:
        # Open a connection-level transaction that never commits to the DB.
        # join_transaction_mode="create_savepoint" makes session.commit() release
        # a savepoint rather than committing the outer transaction, so tearDown
        # can roll everything back cleanly even when service code calls commit().
        self.connection = self.engine.connect()
        self.outer_transaction = self.connection.begin()
        self.db = Session(bind=self.connection, join_transaction_mode="create_savepoint")

    def tearDown(self) -> None:
        self.db.close()
        self.outer_transaction.rollback()
        self.connection.close()

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()
