from flask import Flask
from flask import Blueprint
from flask import flash
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from kitcc_library.book import get_data_from_form, check_form_data, get_book
from kitcc_library.db import get_db
from kitcc_library.auth import login_required
from datetime import datetime, timedelta

blueprint = Blueprint('lend_and_return', __name__, url_prefix='/lend_and_return')

# 書籍の貸出を行う
@blueprint.route('/<int:isbn>/lend_book', methods=('GET',))
@login_required
def lend_book(isbn):
    """
    GET :書籍の貸し出しページに移動
    POST :書籍の貸し借りデータを変更して一覧ページにリダイレクト
    """
    book = get_book(isbn)
    
    # 本が貸し出しできるかどうか(条件を追加するならここに書く)
    error = None
    isNotLend1 = (book['stock'] == 0)
    if isNotLend1:
        error = 'all books are on loan'

    # 本の返却期限
    numberOfWeeksHold = 2
    
    if error:
        flash(error, category='flash message')
    else:
        db = get_db()
        # 本の所蔵数を減らす
        db.execute(
            'UPDATE book SET stock = ? '
            ' WHERE isbn = ?',
            (book['stock']-1, book['ISBN'])
        )

        # userの貸し出し数更新
        db.execute(
            'UPDATE user SET borrow = ? '
            ' WHERE id = ?',
            (g.user['borrow'] + 1, g.user['id'])
        )

        # borrow DBに登録
        today_date = datetime.today()
        return_date = today_date + timedelta(weeks = numberOfWeeksHold)
        dayToStrTemp = "%Y-%m-%d"
        db.execute(
            'INSERT INTO borrow (user_id, book_ISBN, borrow_date, return_date) VALUES (?, ?, ?, ?)',
            (g.user['id'], book['ISBN'], today_date.strftime(dayToStrTemp), return_date.strftime(dayToStrTemp))
        )

        db.commit()
        flash('Lended 『{}』'.format(book['title']), category='flash message')
        
    db = get_db
    

    return redirect(url_for('book.index'))

# 書籍の返却を行う
@blueprint.route('/<int:isbn>/return_book', methods=('GET', 'POST'))
@login_required
def return_book(isbn):
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