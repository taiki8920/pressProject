import os
from src.db import repository as repo


def test_init_and_upsert(tmp_path):
    # run init_db (uses src/db/schema.sql)
    repo.init_db(schema_path="src/db/schema.sql")
    pid = repo.upsert_person("Test Person", wikipedia_summary="summary")
    assert isinstance(pid, int) and pid > 0
