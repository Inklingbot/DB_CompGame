INSERT INTO teams (id, team, objective_percent) VALUES
    (1, 'Wasatch Wardens', 68),
    (2, 'Canyon Foxes', 54),
    (3, 'Salt Flats', 61),
    (4, 'Timber Owls', 47);

INSERT INTO game_instances
    (id, map_id, variant, timer_seconds, played_at, gamestate)
VALUES
    (1, 2, 1, 0,   '2026-09-12 19:00:00', 'results'),
    (2, 5, 3, 0,   '2026-09-19 20:30:00', 'results'),
    (3, 1, 2, 415, '2026-10-14 18:00:00', 'ongoing'),
    (4, 8, 4, 900, '2026-10-20 19:30:00', 'preparing');

INSERT INTO game_teams (game_id, team_id, color) VALUES
    (1, 1, 'Red'),  (1, 2, 'Blue'),
    (2, 3, 'Red'),  (2, 1, 'Blue'),
    (3, 2, 'Red'),  (3, 4, 'Blue'),
    (4, 4, 'Red'),  (4, 3, 'Blue');

INSERT INTO objectives
    (id, game_id, active, type, captured_by_team_id, position_x, position_y)
VALUES
    (1, 1, 0, 'goal', 1,    12.5,  8.0),
    (2, 1, 0, 'zone', 2,    43.0, 31.5),
    (3, 2, 0, 'goal', 3,    19.0, 14.0),
    (4, 2, 0, 'zone', 1,    52.0, 27.0),
    (5, 3, 1, 'goal', NULL,  7.5, 38.0),
    (6, 3, 1, 'zone', 2,    33.0, 21.0),
    (7, 4, 0, 'goal', NULL, 15.0, 15.0),
    (8, 4, 0, 'zone', NULL, 45.0, 45.0);

INSERT INTO traps (id, game_id, tripped, position_x, position_y) VALUES
    (1, 1, 1, 20.0, 10.0),
    (2, 1, 0, 35.0, 22.0),
    (3, 2, 1, 11.5, 41.0),
    (4, 3, 1, 28.0, 18.5),
    (5, 3, 0, 48.0, 33.0),
    (6, 4, 0, 24.0, 24.0);

-- All account values below are fictional and are only for this classroom demo.
INSERT INTO player_identifiers
    (player_id, birthdate, payment_token, email, account_created, password, username)
VALUES
    (1, '1996-04-18', 'demo_tok_1001', 'maya.chen@example.test',   '2025-01-10', 'demo_hash_1', 'MayaC'),
    (2, '1999-11-02', 'demo_tok_1002', 'liam.ortiz@example.test',  '2025-02-14', 'demo_hash_2', 'LiamO'),
    (3, '1997-06-23', 'demo_tok_1003', 'nora.patel@example.test',  '2025-03-07', 'demo_hash_3', 'NoraP'),
    (4, '2000-01-15', 'demo_tok_1004', 'ethan.kim@example.test',   '2025-04-21', 'demo_hash_4', 'EthanK'),
    (5, '1995-09-30', 'demo_tok_1005', 'zoe.martin@example.test',  '2025-05-11', 'demo_hash_5', 'ZoeM'),
    (6, '1998-12-08', 'demo_tok_1006', 'caleb.ng@example.test',    '2025-06-16', 'demo_hash_6', 'CalebN'),
    (7, '2001-03-12', 'demo_tok_1007', 'ava.brooks@example.test',  '2025-07-19', 'demo_hash_7', 'AvaB'),
    (8, '1996-08-27', 'demo_tok_1008', 'jonah.reed@example.test',  '2025-08-24', 'demo_hash_8', 'JonahR');

INSERT INTO cosmetics (player_id, cosmetics_yaml_link) VALUES
    (1, 'cosmetics/mayac.yaml'),
    (2, 'cosmetics/liamo.yaml'),
    (3, 'cosmetics/norap.yaml'),
    (4, 'cosmetics/ethank.yaml'),
    (5, 'cosmetics/zoem.yaml'),
    (6, 'cosmetics/calebn.yaml'),
    (7, 'cosmetics/avab.yaml'),
    (8, 'cosmetics/jonahr.yaml');

INSERT INTO team_membership
    (team_id, player_id, joined_at, left_at, role)
VALUES
    (1, 1, '2025-01-15', NULL, 'captain'),
    (1, 2, '2025-01-20', NULL, 'striker'),
    (2, 3, '2025-02-01', NULL, 'captain'),
    (2, 4, '2025-02-08', NULL, 'defender'),
    (3, 5, '2025-03-10', NULL, 'captain'),
    (3, 6, '2025-03-12', NULL, 'support'),
    (4, 7, '2025-04-05', NULL, 'captain'),
    (4, 8, '2025-04-09', NULL, 'scout');

INSERT INTO player_game_stats
    (game_id, player_id, team_id, kills, deaths, assists)
VALUES
    (1, 1, 1, 12, 5, 8),
    (1, 2, 1,  8, 7, 5),
    (1, 3, 2,  9, 9, 4),
    (1, 4, 2,  6, 8, 7),
    (2, 5, 3, 15, 6, 3),
    (2, 6, 3,  7, 5, 11),
    (2, 1, 1, 10, 9, 6),
    (2, 2, 1,  5, 8, 9),
    (3, 3, 2, 11, 4, 6),
    (3, 4, 2,  4, 6, 10),
    (3, 7, 4,  8, 7, 4),
    (3, 8, 4,  6, 8, 5);
