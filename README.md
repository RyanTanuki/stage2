# CS348 Movie Catalog

A Flask web application for managing a movie database, built for CS348 at Purdue University. Supports full CRUD operations on a movie catalog and a filtered report with summary statistics.

## Features

- **Movies list** — view all movies, sortable by title, year, genre, director, duration, or rating
- **Add / Edit / Delete** movies with dynamic genre and director selection
- **Report** — filter movies by genre, year range, and rating range; displays count, average duration, average rating, and longest/shortest films
- **SQL injection protection** — all queries use parameterized statements; sort column uses a whitelist
- **Indexes** — on genre, rating, release year, genre name, and director name to support report and UI queries

## Tech Stack

- Python 3 + Flask
- SQLite (via Python's built-in `sqlite3` module)
- Bootstrap 5

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/RyanTanuki/cs348-project.git
   cd cs348-project
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask
   ```

4. **Initialize the database** (creates `movies.db` with schema and seed data)
   ```bash
   python init_db.py
   ```

5. **Run the app**
   ```bash
   python app.py
   ```

6. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Project Structure

```
cs348-project/
├── app.py          # Flask routes (CRUD + report)
├── init_db.py      # Database initialization script
├── schema.sql      # Table definitions and indexes
├── seed.sql        # Initial genre, director, and movie data
└── templates/
    ├── base.html        # Shared layout
    ├── movies.html      # Sortable movies list
    ├── movie_form.html  # Add / edit form
    └── report.html      # Filtered report
```

## Database Schema

| Table     | Key columns                                                   |
|-----------|---------------------------------------------------------------|
| Genres    | `genre_id` PK, `name`                                         |
| Directors | `director_id` PK, `name`, `nationality`                       |
| Movies    | `movie_id` PK, `title`, `release_year`, `genre_id` FK, `director_id` FK, `duration_min`, `rating` |
