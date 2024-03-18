import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
import requests
from datetime import date

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py

# Load default config and override config from an environment variable
# TODO use for db path http://flask.pocoo.org/docs/0.12/config/#instance-folders
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))

# FLASKR_SETTINGS points to a config file
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('SELECT title, text, created_at FROM entries ORDER BY id DESC')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/api/search')
def filter_entries():
    searchWord = request.args.get("q")
    db = get_db()
    cur = db.execute(f'SELECT title, text, created_at FROM entries where title like "%{searchWord}%" ORDER BY id DESC')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    
    titel_str = request.form['title']
    text_str = request.form['text']
    created_at_str = str(date.today())

    db = get_db()
    db.execute('INSERT INTO entries (title, text, created_at) VALUES (?, ?, ?)',
               [titel_str, text_str, created_at_str])
    db.commit()
    flash('New entry was successfully posted')
    
    entry = {'title': titel_str, 'text': text_str, 'created_at': created_at_str}
    status_code = post_json_data('https://postman-echo.com/post', payload=entry)
    print(f'HTTP post status: {status_code}')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

def post_json_data(url, payload):
    r = requests.post(url, json=payload)
    return r.status_code


