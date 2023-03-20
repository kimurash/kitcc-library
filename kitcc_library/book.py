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

blueprint = Blueprint('book', __name__)

@blueprint.route('/')
def index():
    """書籍の一覧を取得する"""
    # TODO: 検索機能
    db = get_db()
    books = db.execute(
        'SELECT * FROM book ORDER BY author DESC'
    ).fetchall()

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
    GET :書籍の登録画面に遷移
    POST:書籍を登録して一覧ページにリダイレクト
    """
    if request.method == 'POST':
        attr = get_data_from_form()
        error = check_form_data(attr)

        if error:
            flash(error, category='error')
        else:
            # 書籍の登録
            db = get_db()
            db.execute(
                'INSERT INTO book (title, author, publisher)'
                ' VALUES (?, ?, ?)',
                (attr['title'], attr['author'], attr['publisher'])
            )
            db.commit()
            flash('Registered', category='message')
            return redirect(url_for('book.index'))

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
        error = check_form_data(attr)

        if error:
            flash(error, category='error')
        else:
            # 書籍の変更を保存
            db = get_db()
            db.execute(
                'UPDATE book SET title = ?, author = ?, publisher = ?'
                ' WHERE isbn = ?',
                (attr['title'], attr['author'], attr['publisher'], isbn)
            )
            db.commit()
            flash('Updated', category='message')
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

    flash('Deleted', category='message')
    return redirect(url_for('book.index'))

def get_data_from_form():
    """# リクエストから必要なデータを取得する"""
    attr = dict()
    attr['title'] = request.form['title']
    attr['author'] = request.form['author']
    attr['publisher'] = request.form['publisher']
    return attr

def check_form_data(attr: dict):
    """リクエストに必要なデータが含まれているか確認する"""
    for (key, value) in attr.items():
        if not value:
            return f'{key.capitalize()} is required.'

    return ''
