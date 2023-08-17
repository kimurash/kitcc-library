import os
import tempfile

import pytest
from kitcc_library import create_app
from kitcc_library.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    # バイナリファイルとして読み出す理由
    _data_sql = f.read().decode('utf8')

@pytest.fixture
def app():
    # テスト用のDBを作成する
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True, # テストモードにする
        'DATABASE': db_path, # テスト用のDBを使用する
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)
    
    # 一時的に関数の実行を止めてappを返す
    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='alice', password='alice'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)
