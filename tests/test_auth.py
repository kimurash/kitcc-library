import pytest
from flask import g, session
from kitcc_library.db import get_db


def test_register_delete(client, app, auth):
    # ユーザ登録画面に遷移
    assert client.get('/auth/register_user').status_code == 200

    # ログイン画面にリダイレクト
    response = client.post(
        '/auth/register_user',
        data={'username': 'bob', 'password': 'bob'}
    )
    assert response.headers["Location"] == "/auth/login"

    with app.app_context():
        # ブロック内でget_dbは必ず同じ接続を返す
        # ブロックを抜けるとDBとの接続が切られる

        # ユーザが登録されていることを確認
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'bob'",
        ).fetchone() is not None

    auth.login()

    # ユーザ一覧画面に遷移
    response = client.post('/auth/3/delete_user')
    assert response.headers["Location"] == "/auth/index"

    with app.app_context():
        # ユーザが削除されていることを確認
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'bob'",
        ).fetchone() is None


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('', '', b'Username is required.'),
    ('bob', '', b'Password is required.'),
    ('alice', 'alice', b'already registered.'),
))
def test_register_validate_input(client, username, password, message):
    response = client.post(
        '/auth/register_user',
        data={'username': username, 'password': password}
    )
    assert message in response.data


def test_login(client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers["Location"] == "/"

    with client:
        client.get('/')
        # init_dbでテストユーザを登録する
        assert session['user_id'] == 2
        assert g.user['username'] == 'alice'


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('a', 'alice', b'Incorrect username.'),
    ('alice', 'a', b'Incorrect password.'),
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
