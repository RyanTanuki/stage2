from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Path to the SQLite database file
DB = 'movies.db'


def get_db():
    """Open a connection to the database and return rows as dict-like objects."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row['title']
    return conn


def get_or_create_director(conn, name):
    """
    Look up a director by name. If they don't exist yet, insert them and
    return the new ID. This supports the hybrid director input — the user
    can pick from the datalist OR type a brand-new name.
    """
    name = name.strip()
    row = conn.execute(
        'SELECT director_id FROM Directors WHERE name = ?', (name,)
    ).fetchone()
    if row:
        return row['director_id']
    # New director — insert with no nationality (can be edited later)
    cursor = conn.execute(
        'INSERT INTO Directors (name, nationality) VALUES (?, ?)', (name, '')
    )
    return cursor.lastrowid


# ── Home ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    # Redirect root URL straight to the movies list
    return redirect(url_for('movies'))


# ── Requirement 1: CRUD on Movies ───────────────────────────────────────────

@app.route('/movies')
def movies():
    """
    Display all movies with sortable column headers.
    Query params:
      sort  – column to sort by (default: release_year)
      order – 'asc' or 'desc' (default: desc)
    """
    # Whitelist of allowed sort columns mapped to their SQL expression.
    # Using a whitelist prevents SQL injection via the sort parameter.
    SORTABLE = {
        'title':        'm.title',
        'release_year': 'm.release_year',
        'genre':        'g.name',
        'director':     'd.name',
        'duration_min': 'm.duration_min',
        'rating':       'm.rating',
    }
    sort  = request.args.get('sort',  'release_year')
    order = request.args.get('order', 'desc').lower()

    # Fall back to defaults if invalid values are supplied
    if sort  not in SORTABLE:  sort  = 'release_year'
    if order not in ('asc', 'desc'): order = 'desc'

    # Safe to interpolate because sort comes from the whitelist, not raw user input
    order_clause = f'{SORTABLE[sort]} {order}'

    conn = get_db()
    rows = conn.execute(f'''
        SELECT m.movie_id, m.title, m.release_year,
               g.name AS genre, d.name AS director,
               m.duration_min, m.rating
        FROM Movies m
        JOIN Genres    g ON m.genre_id    = g.genre_id
        JOIN Directors d ON m.director_id = d.director_id
        ORDER BY {order_clause}
    ''').fetchall()
    conn.close()
    return render_template('movies.html', movies=rows, sort=sort, order=order)


@app.route('/movies/add', methods=['GET', 'POST'])
def add_movie():
    """
    GET  – show the blank add-movie form.
           Genre and Director dropdowns are populated from the database
           (not hardcoded), satisfying the dynamic UI requirement.
    POST – insert the new movie into the database and redirect to the list.
    """
    conn = get_db()

    if request.method == 'POST':
        # Explicit transaction: get_or_create_director + INSERT are atomic.
        # SQLite uses DEFERRED isolation by default (SERIALIZABLE) — the write
        # lock is acquired on the first write, so no other connection can
        # interleave between the director lookup and the movie insert.
        with conn:  # __enter__ begins the transaction; __exit__ commits or rolls back
            director_id = get_or_create_director(conn, request.form['director_name'])

            # SQL Injection protection: all user input is passed as ? parameters,
            # never interpolated directly into the query string.
            conn.execute('''
                INSERT INTO Movies (title, release_year, genre_id, director_id, duration_min, rating)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                request.form['title'],
                request.form['release_year'],
                request.form['genre_id'],   # FK → Genres
                director_id,                # FK → Directors (looked up or just created)
                request.form['duration_min'],
                request.form['rating'],
            ))
        conn.close()
        return redirect(url_for('movies'))

    # Build genre dropdown and director datalist from the database — nothing is hardcoded
    genres    = conn.execute('SELECT * FROM Genres    ORDER BY name').fetchall()
    directors = conn.execute('SELECT * FROM Directors ORDER BY name').fetchall()
    conn.close()
    return render_template('movie_form.html', movie=None, genres=genres,
                           directors=directors, current_director='')


@app.route('/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    """
    GET  – show the edit form pre-filled with the movie's current values.
           Dropdowns are populated from the database.
    POST – update the movie row and redirect to the list.
    """
    conn = get_db()

    if request.method == 'POST':
        # Explicit transaction: get_or_create_director + UPDATE are atomic.
        # DEFERRED (SERIALIZABLE) isolation ensures no other writer interleaves.
        with conn:  # __enter__ begins the transaction; __exit__ commits or rolls back
            director_id = get_or_create_director(conn, request.form['director_name'])

            # Parameterized UPDATE — user input never touches the SQL string directly
            conn.execute('''
                UPDATE Movies
                SET title=?, release_year=?, genre_id=?, director_id=?, duration_min=?, rating=?
                WHERE movie_id=?
            ''', (
                request.form['title'],
                request.form['release_year'],
                request.form['genre_id'],
                director_id,                # FK → Directors (looked up or just created)
                request.form['duration_min'],
                request.form['rating'],
                movie_id,   # comes from the URL, cast to int by Flask
            ))
        conn.close()
        return redirect(url_for('movies'))

    # Fetch the existing record and its director's name to pre-fill the form
    movie    = conn.execute('SELECT * FROM Movies WHERE movie_id=?', (movie_id,)).fetchone()
    dir_row  = conn.execute('SELECT name FROM Directors WHERE director_id=?',
                            (movie['director_id'],)).fetchone()
    genres    = conn.execute('SELECT * FROM Genres    ORDER BY name').fetchall()
    directors = conn.execute('SELECT * FROM Directors ORDER BY name').fetchall()
    conn.close()
    return render_template('movie_form.html', movie=movie, genres=genres,
                           directors=directors, current_director=dir_row['name'])


@app.route('/movies/delete/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    """
    Delete a movie row by its primary key.
    Only accepts POST (the delete button submits a small form) to prevent
    accidental deletion via browser pre-fetch of GET links.
    """
    conn = get_db()
    # Parameterized DELETE — movie_id is treated as data, not SQL
    conn.execute('DELETE FROM Movies WHERE movie_id=?', (movie_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('movies'))


# ── Requirement 2: Report with filters ──────────────────────────────────────

@app.route('/report', methods=['GET', 'POST'])
def report():
    """
    GET  – show the filter form with an empty results area.
           The Genre dropdown is built dynamically from the Genres table.
    POST – run the filtered query, compute statistics, and display results.
    """
    conn = get_db()

    # Genre dropdown is always populated from the database (dynamic UI requirement)
    genres = conn.execute('SELECT * FROM Genres ORDER BY name').fetchall()

    results = []
    stats   = None
    filters = {}

    if request.method == 'POST':
        # Read filter values from the submitted form; fall back to wide defaults
        genre_id   = request.form.get('genre_id') or None  # None means "all genres"
        year_from  = int(request.form.get('year_from')    or 1888)
        year_to    = int(request.form.get('year_to')      or 2100)
        rating_min = float(request.form.get('rating_min') or 0)
        rating_max = float(request.form.get('rating_max') or 10)

        # Store filters so the template can re-populate the form fields
        filters = {
            'genre_id':   genre_id,
            'year_from':  year_from,
            'year_to':    year_to,
            'rating_min': rating_min,
            'rating_max': rating_max,
        }

        # Parameterized query — all filter values are bound as ? parameters.
        # The (? IS NULL OR m.genre_id = ?) pattern lets us skip the genre
        # filter when the user selects "All Genres".
        query = '''
            SELECT m.movie_id, m.title, m.release_year,
                   g.name AS genre, d.name AS director,
                   m.duration_min, m.rating
            FROM Movies m
            JOIN Genres    g ON m.genre_id    = g.genre_id
            JOIN Directors d ON m.director_id = d.director_id
            WHERE (? IS NULL OR m.genre_id = ?)
              AND m.release_year BETWEEN ? AND ?
              AND m.rating       BETWEEN ? AND ?
            ORDER BY m.rating DESC
        '''
        results = conn.execute(query, (
            genre_id, genre_id,     # passed twice: once for IS NULL check, once for equality
            year_from, year_to,
            rating_min, rating_max,
        )).fetchall()

        # Compute summary statistics over the matched rows
        if results:
            total      = len(results)
            avg_dur    = sum(r['duration_min'] for r in results) / total
            avg_rating = sum(r['rating']       for r in results) / total
            max_dur    = max(results, key=lambda r: r['duration_min'])
            min_dur    = min(results, key=lambda r: r['duration_min'])
            stats = {
                'total':      total,
                'avg_dur':    round(avg_dur, 1),
                'avg_rating': round(avg_rating, 2),
                'longest':    max_dur['title'],
                'shortest':   min_dur['title'],
            }

    # 'searched' tells the template whether to render the results section at all
    searched = request.method == 'POST'
    conn.close()
    return render_template('report.html', genres=genres, results=results,
                           stats=stats, filters=filters, searched=searched)


if __name__ == '__main__':
    app.run(debug=True)
