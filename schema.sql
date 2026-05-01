PRAGMA foreign_keys = OFF;

CREATE TABLE IF NOT EXISTS Players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER,
    skill_level TEXT CHECK(skill_level IN ('Beginner', 'Intermediate', 'Advanced', 'Pro'))
);

CREATE TABLE IF NOT EXISTS Courts (
    court_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    location TEXT NOT NULL,
    indoor INTEGER NOT NULL DEFAULT 1,
    max_players INTEGER NOT NULL DEFAULT 10
);

CREATE TABLE IF NOT EXISTS Sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    duration INTEGER NOT NULL,
    game_type TEXT NOT NULL CHECK(game_type IN ('Pickup', 'League', 'Practice')),
    UNIQUE (court_id, date, start_time),
    FOREIGN KEY (court_id) REFERENCES Courts(court_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS SessionPlayers (
    session_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    PRIMARY KEY (session_id, player_id),
    FOREIGN KEY (session_id) REFERENCES Sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES Players(player_id) ON DELETE CASCADE
);


INSERT OR IGNORE INTO Players (name, email, age, skill_level) VALUES
    ('Marcus Johnson', 'marcus@email.com', 24, 'Advanced'),
    ('Tyler Brooks',   'tyler@email.com',  19, 'Intermediate'),
    ('Darius King',    'darius@email.com', 28, 'Pro'),
    ('Jaylen Cruz',    'jaylen@email.com', 22, 'Beginner'),
    ('Chris Wade',     'chris@email.com',  31, 'Advanced');

INSERT OR IGNORE INTO Courts (name, location, indoor, max_players) VALUES
    ('Court A', 'Main Gym - North', 1, 10),
    ('Court B', 'Main Gym - South', 1, 10),
    ('Court C', 'Recreation Center', 1, 8),
    ('Outdoor 1', 'East Campus', 0, 10),
    ('Outdoor 2', 'West Campus', 0, 10);

INSERT OR IGNORE INTO Sessions (court_id, date, start_time, duration, game_type) VALUES
    (1, '2026-03-01', '09:00', 60,  'Pickup'),
    (1, '2026-03-05', '14:00', 90,  'League'),
    (2, '2026-03-10', '10:00', 120, 'Practice'),
    (3, '2026-03-15', '16:00', 60,  'Pickup'),
    (4, '2026-03-20', '08:00', 75,  'League'),
    (1, '2026-03-22', '11:00', 90,  'Pickup'),
    (2, '2026-03-25', '15:00', 60,  'Practice');

-- Indexes
-- speeds up the filtering on reports by the date range
CREATE INDEX IF NOT EXISTS idx_sessions_date
    ON Sessions(date);

-- speeds up the filtering on reports by the type of game
CREATE INDEX IF NOT EXISTS idx_sessions_game_type
    ON Sessions(game_type);

-- speeds up lookups of players by the player_id
CREATE INDEX IF NOT EXISTS idx_sessionplayers_player
    ON SessionPlayers(player_id);

-- speeds up the loading of the dropdowns by looking up the players
CREATE INDEX IF NOT EXISTS idx_players_name
    ON Players(name);

INSERT OR IGNORE INTO SessionPlayers (session_id, player_id) VALUES
    (1, 1), (1, 2), (1, 3),
    (2, 1), (2, 4),
    (3, 2), (3, 3), (3, 5),
    (4, 1), (4, 2), (4, 4), (4, 5),
    (5, 3), (5, 4),
    (6, 1), (6, 3),
    (7, 2), (7, 5);

PRAGMA foreign_keys = ON;