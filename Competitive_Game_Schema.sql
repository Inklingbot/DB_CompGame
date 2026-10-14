PRAGMA foreign_keys = ON;

CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    team TEXT NOT NULL UNIQUE,
    objective_percent INTEGER NOT NULL DEFAULT 0
        CHECK (objective_percent BETWEEN 0 AND 100)
);

CREATE TABLE game_instances (
    id INTEGER PRIMARY KEY,
    map_id INTEGER NOT NULL CHECK (map_id BETWEEN 1 AND 10),
    variant INTEGER NOT NULL CHECK (variant BETWEEN 1 AND 10),
    timer_seconds INTEGER NOT NULL CHECK (timer_seconds >= 0),
    played_at TEXT NOT NULL,
    gamestate TEXT NOT NULL
        CHECK (gamestate IN ('ongoing', 'results', 'preparing'))
);

CREATE TABLE game_teams (
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    color TEXT NOT NULL CHECK (color IN ('Red', 'Blue')),
    PRIMARY KEY (game_id, team_id),
    UNIQUE (game_id, color),
    FOREIGN KEY (game_id) REFERENCES game_instances (id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

CREATE TABLE objectives (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    type TEXT NOT NULL CHECK (type IN ('goal', 'zone')),
    captured_by_team_id INTEGER,
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    FOREIGN KEY (game_id) REFERENCES game_instances (id) ON DELETE CASCADE,
    FOREIGN KEY (game_id, captured_by_team_id)
        REFERENCES game_teams (game_id, team_id)
);

CREATE TABLE traps (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    tripped INTEGER NOT NULL CHECK (tripped IN (0, 1)),
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    FOREIGN KEY (game_id) REFERENCES game_instances (id) ON DELETE CASCADE
);

CREATE TABLE player_identifiers (
    player_id INTEGER PRIMARY KEY,
    birthdate TEXT NOT NULL,
    payment_token TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    account_created TEXT NOT NULL,
    password TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE cosmetics (
    player_id INTEGER PRIMARY KEY,
    cosmetics_yaml_link TEXT NOT NULL,
    FOREIGN KEY (player_id)
        REFERENCES player_identifiers (player_id) ON DELETE CASCADE
);

CREATE TABLE team_membership (
    team_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    joined_at TEXT NOT NULL,
    left_at TEXT,
    role TEXT NOT NULL,
    PRIMARY KEY (team_id, player_id, joined_at),
    CHECK (left_at IS NULL OR left_at >= joined_at),
    FOREIGN KEY (team_id) REFERENCES teams (id),
    FOREIGN KEY (player_id) REFERENCES player_identifiers (player_id)
);

CREATE TABLE player_game_stats (
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    kills INTEGER NOT NULL DEFAULT 0 CHECK (kills >= 0),
    deaths INTEGER NOT NULL DEFAULT 0 CHECK (deaths >= 0),
    assists INTEGER NOT NULL DEFAULT 0 CHECK (assists >= 0),
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (player_id) REFERENCES player_identifiers (player_id),
    FOREIGN KEY (game_id, team_id)
        REFERENCES game_teams (game_id, team_id)
);

CREATE VIEW player_stats AS
SELECT
    p.player_id,
    COALESCE(SUM(s.kills), 0) AS total_kills,
    COALESCE(SUM(s.assists), 0) AS total_assists,
    COALESCE(SUM(s.deaths), 0) AS total_deaths,
    COUNT(s.game_id) AS total_games
FROM player_identifiers AS p
LEFT JOIN player_game_stats AS s ON s.player_id = p.player_id
GROUP BY p.player_id;

CREATE INDEX idx_game_teams_team_id ON game_teams (team_id);
CREATE INDEX idx_objectives_game_id ON objectives (game_id);
CREATE INDEX idx_traps_game_id ON traps (game_id);
CREATE INDEX idx_membership_player_id ON team_membership (player_id);
CREATE INDEX idx_player_game_stats_team_id ON player_game_stats (team_id);
