import os
import sqlite3

import click
from flask import Flask
from flask import current_app
from flask import g
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

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

    # テストユーザの情報を取得
    load_dotenv()
    test_user_name = os.getenv('TEST_USER_NAME')
    test_user_password = os.getenv('TEST_USER_PASSWORD')
    password_hash = generate_password_hash(test_user_password)

    # テストユーザを登録
    db.execute(
        "INSERT INTO user (username, password)"
        f"VALUES ('{test_user_name}', '{password_hash}')"
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
