import os

from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev', # 運用時はconfig.pyに記述する
        DATABASE=os.path.join(app.instance_path, 'kitcc_library.db'),
    )

    if test_config is None:
        # instance/config.pyで標準設定を上書きする
        app.config.from_pyfile('config.py', silent=True)
    else:
        # テスト時の設定を読み込む
        app.config.from_mapping(test_config)

    # instanceディレクトリが無ければ作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app) # DBに関する設定

    # ログイン機能の追加
    from . import auth
    app.register_blueprint(auth.blueprint)

    # 書籍管理機能の追加
    from . import book
    app.register_blueprint(book.blueprint)

    # エンドポイント'index'とURL'/'を紐づける
    # url_for('index')で'/'が生成される
    app.add_url_rule('/', endpoint='index')

    # テスト用のページ
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('img/favicon.ico')

    return app
