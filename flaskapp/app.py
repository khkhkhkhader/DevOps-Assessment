from flask import (
    Flask, render_template, json,
    request, redirect, session, url_for, jsonify
)
from flaskext.mysql import MySQL
import os
import logging
import sys
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "bucketlist-flask",
            "event": getattr(record, "event", "application_log"),
            "message": record.getMessage(),
        })


log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(JsonFormatter())
app_logger = logging.getLogger("bucketlist")
app_logger.handlers = [log_handler]
app_logger.setLevel(logging.INFO)
app_logger.propagate = False


app = Flask(__name__)
def read_secret(name):
    path = os.getenv(name + '_FILE')
    if path:
        with open(path, encoding='utf-8') as secret_file:
            return secret_file.read().strip()
    return os.environ[name]

app.secret_key = read_secret('FLASK_SECRET_KEY')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true' 

mysql = MySQL()

# MySQL configurations (from env variables)
app.config['MYSQL_DATABASE_USER'] = os.getenv('MYSQL_DATABASE_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = read_secret('MYSQL_DATABASE_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('MYSQL_DATABASE_DB')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('MYSQL_DATABASE_HOST')

mysql.init_app(app)

# External prefix presented by ingress
BASE_PATH = ""


@app.context_processor
def inject_base_path():
    """Make BASE_PATH available in Jinja templates"""
    return dict(BASE_PATH=BASE_PATH)


def redirect_with_base(endpoint, **values):
    """
    Build an app-internal URL with url_for, then prefix with BASE_PATH
    so the browser is redirected to /flask/... (what ingress exposes).
    """
    return redirect(BASE_PATH + url_for(endpoint, **values))


@app.route("/")
def main():
    return render_template('index.html')


@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')


@app.route('/showSignIn')
def showSignIn():
    return render_template('signin.html')


@app.route('/signUp', methods=['POST'])
def signUp():
    conn, cursor = None, None
    try:
        _name = request.form.get('inputName')
        _email = request.form.get('inputEmail')
        _password = request.form.get('inputPassword')

        if _name and _email and _password:
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_createUser', (_name, _email, generate_password_hash(_password)))
            data = cursor.fetchall()

            if len(data) == 0:
                conn.commit()
                return jsonify({'message': 'User created successfully!'}), 200
            return jsonify({'error': str(data[0])}), 400
        return jsonify({'error': 'Enter all required fields'}), 400
    except Exception as e:
        app_logger.error("Signup failed: %s", type(e).__name__, extra={"event": "signup_error"})
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@app.route('/validateLogin', methods=['POST'])
def validateLogin():
    conn, cursor = None, None
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.callproc('sp_validateLogin', (_username,))
        data = cursor.fetchall()

        if len(data) > 0 and check_password_hash(data[0][3], _password):
            session['user'] = data[0][0]
            return redirect_with_base('userHome')

        return render_template(
            'error.html',
            error='Wrong Email address or Password'
        )
    except Exception as e:
        app_logger.error("Login failed: %s", type(e).__name__, extra={"event": "login_error"})
        return render_template('error.html', error='Internal server error'), 500
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@app.route('/userHome')
def userHome():
    if session.get('user'):
        return render_template('userHome.html')
    return render_template('error.html', error='Unauthorized Access')


@app.route('/getWish')
def getWish():
    conn, cursor = None, None
    try:
        if session.get('user'):
            _user = session.get('user')
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetWishByUser', (_user,))
            wishes = cursor.fetchall()

            wishes_dict = [
                {
                    'Id': wish[0],
                    'Title': wish[1],
                    'Description': wish[2],
                    'Date': wish[4]
                }
                for wish in wishes
            ]
            return json.dumps(wishes_dict)

        return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        app_logger.error("Get wish failed: %s", type(e).__name__, extra={"event": "get_wish_error"})
        return render_template('error.html', error='Internal server error'), 500
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@app.route('/addWish', methods=['POST'])
def addWish():
    conn, cursor = None, None
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addWish', (_title, _description, _user))
            data = cursor.fetchall()

            if len(data) == 0:
                conn.commit()
                return redirect_with_base('userHome')

            return render_template('error.html', error='An error occurred!')

        return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        app_logger.error("Add wish failed: %s", type(e).__name__, extra={"event": "add_wish_error"})
        return render_template('error.html', error='Internal server error'), 500
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect_with_base('main')


@app.route('/showAddWish')
def showAddWish():
    if session.get('user'):
        return render_template('addWish.html')
    return render_template('error.html', error='Unauthorized Access')


@app.route('/healthz')
def healthz():
    return "ok", 200


@app.route('/readiness')
def readiness():
    """Readiness probe that checks database connectivity"""
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return "ready", 200
    except Exception as e:
        app_logger.warning("Readiness check failed: %s", type(e).__name__, extra={"event": "readiness_failed"})
        return "not ready", 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
