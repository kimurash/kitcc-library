import sqlite3

import pytest
from kitcc_library.db import get_db


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()

    with pytest.raises(sqlite3.ProgrammingError) as err:
        db.execute('SELECT 1')

    # DBとの接続は切られている
    assert 'closed' in str(err.value)


def test_init_db_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    # 一時的にinit_dbをfake_init_dbに置き換える
    monkeypatch.setattr('kitcc_library.db.init_db', fake_init_db)
    result = runner.invoke(args=['init-db'])
    assert 'Initialized' in result.output
    assert Recorder.called