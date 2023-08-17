from kitcc_library import create_app


def test_config():
    # testingはテストモードのフラグ
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    # レスポンスはバイト文字列で返される
    assert response.data == b'Hello, World!'