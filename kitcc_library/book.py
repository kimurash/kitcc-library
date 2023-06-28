from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from werkzeug.exceptions import abort

from flask_paginate import Pagination
from flask_paginate import get_page_parameter

from kitcc_library.auth import login_required
from kitcc_library.db import get_db

import requests

PER_PAGE = 20 # 1ページに表示する冊数

blueprint = Blueprint('book', __name__)

@blueprint.route('/', methods=('GET', 'POST'))
def index():
    """
    GET :登録済みの全書籍の取得
    POST:条件に合った書籍を取得して一覧ページに表示
    """
    db = get_db()
    if request.method == 'GET':
        books = db.execute(
            'SELECT * FROM book ORDER BY author DESC'
        ).fetchall()
    elif request.method == 'POST':
        attr = get_data_from_form()
        query, args = create_sql_sentence(attr)
        books = db.execute(query, tuple(args)).fetchall()

    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(
        page=page, per_page=PER_PAGE, total=len(books),
        record_name='books', css_framework='bootstrap5'
    )

    return render_template(
        'book/index.html',
        books=books[(page - 1) * PER_PAGE:page * PER_PAGE],
        pagination=pagination
    )

@blueprint.route('/register_book', methods=('GET', 'POST'))
@login_required
def register_book():
    """
    GET :書籍の検索結果の表示
    POST:書籍を登録して一覧ページへリダイレクト
    """
    if request.method == 'POST':
        attr = get_data_from_form()
        db = get_db()
        same_book = db.execute(
            'SELECT * FROM book WHERE isbn = ?', (attr['ISBN'],)
        ).fetchone()

        if same_book is None: # 新規登録
            db.execute(
                'INSERT INTO book (title, author, publisher, ISBN)'
                ' VALUES (?, ?, ?, ?)',
                (attr['title'], attr['author'], attr['publisher'], attr['ISBN'])
            )
        else: # 登録済み
            db.execute(
                'UPDATE book SET stock = ? WHERE isbn = ?',
                (same_book['stock']+1, attr['ISBN'])
            )
        db.commit()

        flash('Registered', category='flash message')
        return redirect(url_for('book.index'))

    # 書籍の検索
    attr = get_data_from_args()
    page = request.args.get(get_page_parameter(), type=int, default=1)
    (books, total_items) = search_books_from_API(attr, page)

    pagination = Pagination(
        page=page, per_page=PER_PAGE, total=total_items,
        record_name='books', css_framework='bootstrap5'
    )

    return render_template('book/register.html', books=books, pagination=pagination)

@blueprint.route('/<int:isbn>/update_book', methods=('GET', 'POST'))
@login_required
def update_book(isbn):
    """
    GET :書籍の編集画面に遷移
    POST:書籍の変更を保存して一覧ページへリダイレクト
    """
    book = get_book(isbn)

    if request.method == 'POST':
        attr = get_data_from_form()
        attr['stock'] = request.form['stock']
        error = check_form_data(attr)

        if error:
            flash(error, category='flash error')
        else:
            # 書籍の変更を保存
            db = get_db()
            db.execute(
                'UPDATE book SET title = ?, author = ?, publisher = ?, stock = ? '
                ' WHERE isbn = ?',
                (attr['title'], attr['author'], attr['publisher'], attr['stock'], isbn)
            )
            db.commit()
            flash('Updated', category='flash message')
            return redirect(url_for('book.index'))

    return render_template('book/update.html', book=book)

# 削除用の画面はないのでGETメソッドはルーティングしない
@blueprint.route('/<int:isbn>/delete_book', methods=('POST',))
@login_required
def delete_book(isbn):
    """書籍を削除して一覧ページへリダイレクト"""
    get_book(isbn)
    db = get_db()
    db.execute('DELETE FROM book WHERE isbn = ?', (isbn,))
    db.commit()

    flash('Deleted', category='flash message')
    return redirect(url_for('book.index'))

# 書籍の貸出を行う
@blueprint.route('/<int:isbn>/lend_book', methods=('GET', 'POST'))
@login_required
def lend_book():
    if request.method == 'POST':
        attr = get_data_from_form()
        error = check_form_data(attr)
        book = get_book(attr['isbn'])
        if book['stock'] == 0:
            error = 'all books are on loan'
        if error:
            flash(error, category='flash message')
        else:
            db = get_db()
            db.execute(
                'UPDATE book SET stock = ? '
                ' WHERE isbn = ?',
                (book['stock']-1, book['isbn'])
            )
            db.commit()
            flash('Lended', category='flash message')
            return redirect(url_for('book.index'))
    return render_template('book/lend.html', book=book)

# 書籍の返却を行う
@blueprint.route('/<int:isbn>/return_book', methods=('GET', 'POST'))
@login_required
def return_book():
    if request.method == 'POST':
        attr = get_data_from_form()
        error = check_form_data(attr)
        book = get_book(attr['isbn'])
        if error:
            flash(error, category='flash message')
        else:
            db = get_db()
            db.execute(
                'UPDATE book SET stock = ? '
                ' WHERE isbn = ?',
                (book['stock']+1, book['isbn'])
            )
            db.commit()
            flash('Returned', category='flash message')
            return redirect(url_for('book.index'))
    return render_template('book/return.html', book=book)

def get_book(isbn):
    book = get_db().execute(
        'SELECT * FROM book WHERE isbn = ?', (isbn,)
    ).fetchone()

    if book is None:
        abort(404, f"Book ISBN {isbn} doesn't exist.")

    return book

def search_books_from_API(attr: dict, page):
    """
    Google Books APIsからisbnに合う本を検索してJSON形式で取得 -> 辞書型に整形
    ISBN_13がないものは省く
    """
    # リクエストURLの生成
    url = 'https://www.googleapis.com/books/v1/volumes?maxResults=' + str(PER_PAGE) + '&startIndex=' + str((page - 1) * PER_PAGE) + '&q='
    for (key, value) in attr.items():
        if value:
            if key == 'ISBN':
                url = url + '+' + key.lower() + ':' + value
            else:
                url = url + '+in' + key + ':' + value

    # APIにリクエストを投げる
    response = requests.get(url).json()
    total_items = int(response.get('totalItems', '0'))
    items_list = response.get('items')
    books = []

    # totalItems != 0でもitemsがない場合がある
    # e.g.(https://www.googleapis.com/books/v1/volumes?maxResults=40&q=+intitle:%EF%BC%9A&startIndex=280)
    if items_list is None:
        return (books, total_items)

    # レスポンスから書籍の情報を抽出
    for item in items_list:
        info = item.get('volumeInfo')
        # ISBN_13をisbnに取得
        isbn = None
        for isbn_X in info.get('industryIdentifiers', []):
            if isbn_X.get('type') == 'ISBN_13':
                isbn = isbn_X.get('identifier')
                break

        if isbn is None:
            continue

        authors_list = info.get('authors')
        books.append({
            'title': info.get('title'),
            'author': ','.join(authors_list) if authors_list is not None else None,
            'publisher': info.get('publisher'),
            'ISBN': isbn
        })

    return (books, total_items)

def create_sql_sentence(attr: dict):
    """
    入力条件に応じたSQL文を生成
    入力条件がなければ登録済みの書籍を全て検索
    """
    query = 'SELECT * FROM book WHERE '
    args = []
    for (key, value) in attr.items():
        if value:
            if len(args) != 0:
                query = query + 'AND '
            if key == 'ISBN':
                query = query + key + ' = ? '
                args.append(str(value))
            else:
                query = query + key + ' LIKE ? '
                args.append('%' + str(value) + '%')

    if (len(args) == 0):
        return ('SELECT * FROM book ORDER BY author DESC', args)

    return (query, args)

# GETメソッドのとき
def get_data_from_args():
    attr = dict()
    attr['title'] = request.args.get('title')
    attr['author'] = request.args.get('author')
    attr['publisher'] = request.args.get('publisher')
    attr['ISBN'] = request.args.get('ISBN')
    return attr

# POSTメソッドのとき
def get_data_from_form():
    attr = dict()
    attr['title'] = request.form.get('title')
    attr['author'] = request.form.get('author')
    attr['publisher'] = request.form.get('publisher')
    attr['ISBN'] = request.form.get('ISBN')
    return attr

def check_form_data(attr: dict):
    """リクエストに必要なデータが含まれているか確認する"""
    for (key, value) in attr.items():
        if not value:
            return f'{key.capitalize()} is required.'

    return ''
