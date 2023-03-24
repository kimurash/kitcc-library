from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from werkzeug.exceptions import abort

from kitcc_library.auth import login_required
from kitcc_library.db import get_db

import json
import requests

blueprint = Blueprint('book', __name__)

@blueprint.route('/', methods=('GET', 'POST'))
def index():
    """書籍の一覧を取得する"""
    """
    GET :登録済みの全書籍の取得
    POST:条件に合った書籍を取得し、一覧ページに表示
    """
    # TODO: 検索機能
    db = get_db()
    if request.method == 'GET':
        books = db.execute(
            'SELECT * FROM book ORDER BY author DESC'
        ).fetchall()
    elif request.method == 'POST':
        attr = get_data_from_form()
        books = db.execute(create_sql_centence(attr)).fetchall()
    return render_template('book/index.html', books=books)

def get_book(isbn):
    book = get_db().execute(
        'SELECT * FROM book WHERE isbn = ?', (isbn,)
    ).fetchone()

    if book is None:
        abort(404, f"Book ISBN {isbn} doesn't exist.")

    return book

@blueprint.route('/create_book', methods=('GET', 'POST'))
@login_required
def create_book():
    """
    GET :書籍の検索画面に遷移
    POST:書籍を検索して表示
    """
    if request.method == 'POST':
        attr = get_data_from_form()
        # error = check_form_data(attr)
        error = None #errorは考えなくていい?

        if error:
            flash(error, category='flash error')
        else:
            # 書籍の検索・表示
            books = search_books_from_API(attr)
            return render_template('book/create.html', books=books)

    return render_template('book/create.html')


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

def get_data_from_form():
    """# リクエストから必要なデータを取得する"""
    attr = dict()
    attr['title'] = request.form['title']
    attr['author'] = request.form['author']
    attr['publisher'] = request.form['publisher']
    attr['ISBN'] = request.form['ISBN']
    return attr

def check_form_data(attr: dict):
    """リクエストに必要なデータが含まれているか確認する"""
    for (key, value) in attr.items():
        if not value:
            return f'{key.capitalize()} is required.'

    return ''

def search_books_from_API(attr: dict):
    """
    Google Books APIsからisbnに合う本を1冊だけ検索し、JSON形式で取得。辞書型に整形
    現状、ISBN_13がないものは省く
    """
    max_results = 40 #ページ分割するなら、引数に指定し、create_bookで制御が丸い?
    url = 'https://www.googleapis.com/books/v1/volumes?maxResults=' + str(max_results) + '&q='
    for (key, value) in attr.items():
        if value:
            if key == 'ISBN':
                url = url + '+' + key.lower() + ':' + value
            else:
                url = url + '+in' + key + ':' + value
    response = requests.get(url).json()
    num_items = int(response.get('totalItems'))
    books = []
    for index in range((num_items // max_results) + int(bool(num_items % max_results))):
        temp_url = url + '&startIndex=' + str(index * max_results)
        # print(temp_url)
        temp_response = requests.get(temp_url).json()
        items_list = temp_response.get('items')
        if items_list is None:
            break
        for item in items_list: #totalItems != 0でも、itemsがない場合がある。e.g.(https://www.googleapis.com/books/v1/volumes?maxResults=40&q=+intitle:%EF%BC%9A&startIndex=280)
            info = item.get('volumeInfo')
            # ISBN_13をisbnに取得
            isbn = None
            for isbn_X in info.get('industryIdentifiers') if info.get('industryIdentifiers') is not None else []:
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
                'ISBN': isbn})
    return books

def search_book_from_API(isbn):
    """
    Google Books APIsからisbnに合う本を1冊だけ検索し、JSON形式で取得。辞書型に整形
    """
    url = 'https://www.googleapis.com/books/v1/volumes?maxResults=1&q=isbn:' + str(isbn)
    response = requests.get(url).json()
    info = response.get('items')[0].get('volumeInfo')
    authors_list = info.get('authors')
    book = {
        'title': info.get('title'),
        'author': ','.join(authors_list) if authors_list is not None else None,
        'publisher': info.get('publisher'),
        'ISBN': isbn}
    return book

def create_sql_centence(attr: dict):
    """入力条件に応じたSQL文を生成。入力条件がないなら、登録済みの書籍を全て検索"""
    sql = 'SELECT * FROM book WHERE '
    flag = 0
    for (key, value) in attr.items():
        if value:
            if flag != 0:
                sql = sql + 'AND '
            if key == 'ISBN': #isbnを文字列型にしたとき''で囲むのに気を付けた方が良い(現状、数字以外が来るとエラー).
                sql = sql + key + ' = ' + value + ' '
            else:
                sql = sql + key + ' LIKE \'%%' + value + '%%\' '
            flag += 1
    if (flag == 0):
        return f'SELECT * FROM book ORDER BY author DESC'
    return sql

@blueprint.route('/<int:isbn>/register_book')
@login_required
def register_book(isbn):
    # 書籍の登録(ToDo:isbn情報登録の追加)
    attr = search_book_from_API(isbn)
    db = get_db()
    same_book = db.execute(
        'SELECT * FROM book WHERE isbn = ?', (isbn,)
    ).fetchone() #get_book()で良さそう
    if same_book is None:
        db.execute(
            'INSERT INTO book (title, author, publisher, ISBN)'
            ' VALUES (?, ?, ?, ?)',
            (attr['title'], attr['author'], attr['publisher'], isbn)
        )
    else:
        db.execute(
            'UPDATE book SET stock = ?'
            ' WHERE isbn = ?',
            (same_book['stock']+1, isbn)
        )
    db.commit()
    flash('Registered', category='flash message')
    return redirect(url_for('book.index'))