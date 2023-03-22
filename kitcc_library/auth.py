import functools

from flask import Blueprint
from flask import g
from flask import request
from flask import session
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from kitcc_library.db import get_db

blueprint = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    """未ログインであればログインページにリダイレクト"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Please log in before', category='flash warning')
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

# blueprint内外に関わらず全リクエストの前に実行される
@blueprint.before_app_request
def load_logged_in_user():
    """ログイン済みであればユーザー情報をグローバル変数に格納する"""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@blueprint.route('/index')
@login_required
def index():
    """ログイン済みユーザ以外のユーザを取得する"""
    db = get_db()
    users = db.execute(
        'SELECT * FROM user WHERE id <> ?  ORDER BY username DESC',
        (g.user['id'],)
    ).fetchall()

    return render_template('auth/index.html', users=users)

@blueprint.route('/register_user', methods=('GET', 'POST'))
def register_user():
    """
    GET :ユーザ登録画面に遷移
    POST:ユーザを登録してログイン画面にリダイレクト
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # ユーザ名とパスワードの確認
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                # ユーザの登録
                db.execute(
                    'INSERT INTO user (username, password) VALUES (?, ?)',
                    (username, generate_password_hash(password)), # パスワードはハッシュ化して記録
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                flash('Registered', category='flash message')
                return redirect(url_for("auth.login"))

        flash(error, category='flash error') # エラーメッセージを表示

    return render_template('auth/register.html')

@blueprint.route('/<int:id>/delete_user', methods=('POST',))
@login_required
def delete_user(id):
    """ユーザを削除して一覧ページへリダイレクト"""
    # TODO: ユーザの存在確認
    db = get_db()
    db.execute('DELETE FROM user WHERE id = ?', (id,))
    db.commit()

    flash('Deleted', category='flash message')
    return redirect(url_for('auth.index'))

@blueprint.route('/login', methods=('GET', 'POST'))
def login():
    """
    GET :ログイン画面に遷移
    POST:ログイン後,蔵書一覧ページにリダイレクト
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # DBからユーザ情報を取得
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        # ユーザ名とパスワードの確認
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            # ユーザIDをCookieに保存する -> 以降のリクエストで使えるようになる
            session.clear()
            session['user_id'] = user['id']

            flash(f'Logged in as {username}', category='flash info')
            return redirect(url_for('index'))

        flash(error, category='flash error')

    return render_template('auth/login.html')

@blueprint.route('/logout')
def logout():
    session.clear()
    flash('Logged out', category='flash message')
    return redirect(url_for('index'))
