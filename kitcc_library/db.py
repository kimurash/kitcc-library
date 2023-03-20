import sqlite3

import click
from flask import Flask
from flask import current_app
from flask import g

def init_app(app: Flask):
    # レスポンスを返した後に呼び出す関数を登録
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

@click.command('init-db')
def init_db_command():
    init_db() # 既存のデータを削除して表を新規作成する
    click.echo('Initialized the database.')

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    # テストユーザを登録
    db.execute(
        "INSERT INTO user (username, password)"
        "VALUES ('shunsei', 'pbkdf2:sha256:260000$P9wjL1bRDRjVBJjo$048651989cff8c8317e7bd3720f58c9c24dbbb914bce905448e33bc2e8504698')"
    )
    db.commit()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # 列に名前でアクセスできるようにする
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(exc=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
