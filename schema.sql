CREATE TABLE IF NOT EXISTS Genres (
    genre_id INTEGER PRIMARY KEY,
    name     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Directors (
    director_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    nationality TEXT
);

CREATE TABLE IF NOT EXISTS Movies (
    movie_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    release_year INTEGER,
    genre_id     INTEGER REFERENCES Genres(genre_id),
    director_id  INTEGER REFERENCES Directors(director_id),
    duration_min INTEGER,
    rating       REAL
);

-- Indexes to support the report filters and dynamic UI queries

-- Report filter: WHERE (genre_id = ?) and JOIN to Genres table
CREATE INDEX IF NOT EXISTS idx_movies_genre_id     ON Movies(genre_id);

-- Report filter: AND rating BETWEEN ? AND ? / ORDER BY rating DESC
CREATE INDEX IF NOT EXISTS idx_movies_rating       ON Movies(rating);

-- Report filter: AND release_year BETWEEN ? AND ?
CREATE INDEX IF NOT EXISTS idx_movies_release_year ON Movies(release_year);

-- Dynamic genre dropdown: SELECT * FROM Genres ORDER BY name
CREATE INDEX IF NOT EXISTS idx_genres_name         ON Genres(name);

-- Director datalist population (ORDER BY name) and get_or_create_director lookup (WHERE name = ?)
CREATE INDEX IF NOT EXISTS idx_directors_name      ON Directors(name);
