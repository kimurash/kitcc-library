from flask import Flask
from flask import current_app
from flask import g

from kitcc_library.db import get_db

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