# kitcc_library
部室の書籍をデータベース化するプロジェクト

## 使用している技術
- [Poetry](https://python-poetry.org/)
- [Flask](https://flask.palletsprojects.com/en/2.2.x/)
- [Requests](https://requests.readthedocs.io/en/latest/)
- [flask-paginate](https://pythonhosted.org/Flask-paginate/)
- [QuaggaJS](https://serratus.github.io/quaggaJS/)

Poetryを使用してパッケージを管理しています．
Poetryがインストールされた環境で`install`コマンドを実行すると
必要なパッケージがインストールされます．
```
poetry install
```

## ディレクトリ構成
```
├─kitcc_library
│  │  auth.py
│  │  book.py
│  │  db.py
│  │  schema.sql
│  │  __init__.py
│  │
│  ├─static
│  │  ├─css
│  │  ├─img
│  │  └─js
│  │
│  └─templates
│     ├─auth
│     └─book
│
└─tests
```

## 動作確認の方法
- データベースの初期化
```
flask --app kitcc_library init-db
```

- アプリの起動
```
flask --app kitcc_library run [--debug]
```
