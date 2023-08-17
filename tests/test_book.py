import pytest
from kitcc_library.db import get_db

SAMPLE_ISBN = '9784873115658'

def test_index(client, auth):
    response = client.get('/')
    assert b"Book List" in response.data
    assert b"Log In" in response.data

    auth.login()

    response = client.get('/')
    assert b'User List' in response.data
    assert b'Log Out' in response.data
    # f(format)とb(byte)は同時に指定できない
    assert b'href="/9784873115658/update_book"' in response.data

    # 日本語はASCII文字でないのでバイト列として扱えない
    assert 'リーダブルコード' in response.get_data(as_text=True)
    assert 'オライリー・ジャパン' in response.get_data(as_text=True)


@pytest.mark.parametrize('path', (
    '/register_book',
    f'/{SAMPLE_ISBN}/update_book',
    f'/{SAMPLE_ISBN}/delete_book',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize('path', (
    '/9784297127831/update_book',
    '/9784297127831/delete_book',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_register(client, auth, app):
    auth.login()
    assert client.get('/register_book').status_code == 200

    # 登録済みの本を登録
    client.post('/register_book',
                data={
                    'ISBN': SAMPLE_ISBN,
                    'title': 'リーダブルコード',
                    'author': 'Dustin Boswell',
                    'publisher': 'オライリー・ジャパン',
                })

    with app.app_context():
        db = get_db()

        stock = db.execute(f"SELECT stock FROM book WHERE isbn = '{SAMPLE_ISBN}'").fetchone()[0]
        assert stock == 2

        count = db.execute('SELECT COUNT(ISBN) FROM book').fetchone()[0]
        assert count == 1


def test_update(client, auth, app):
    auth.login()
    assert client.get(f'/{SAMPLE_ISBN}/update_book').status_code == 200
    client.post(f'/{SAMPLE_ISBN}/update_book',
                data={
                    'ISBN': SAMPLE_ISBN,
                    'title': 'リーダブルコード',
                    'author': 'Trevor Foucher',
                    'publisher': 'オライリー・ジャパン',
                    'stock': 1,
                })

    with app.app_context():
        db = get_db()
        book = db.execute(f"SELECT * FROM book WHERE isbn = '{SAMPLE_ISBN}'").fetchone()
        assert book['author'] == 'Trevor Foucher'


@pytest.mark.parametrize('path', (
    # 大規模化に備えてパスを引数化しておく
    f'/{SAMPLE_ISBN}/update_book',
))
def test_update_validate(client, auth, path):
    auth.login()
    response = client.post(path,
                           data={
                                'ISBN': SAMPLE_ISBN,
                                'title': '',
                                'author': '',
                                'publisher': '',
                                'stock': 1
                            })
    assert b'Title is required.' in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post(f'/{SAMPLE_ISBN}/delete_book')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        book = db.execute(f"SELECT * FROM book WHERE isbn = '{SAMPLE_ISBN}'").fetchone()
        assert book is None
