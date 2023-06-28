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
        "VALUES ('kitcclib', 'pbkdf2:sha256:260000$1xxmjFqBIFvY19KR$ca2cc058c971dd43aa53a4e7bc53144fadb185b31680178ec22132e730b31a5d')"
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
