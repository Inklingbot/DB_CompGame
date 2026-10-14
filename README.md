# Competitive Game Database Assistant

This Python command-line app lets a game employee ask plain-language questions
about a competitive game database. It asks an OpenAI model for a read-only
SQLite query, runs that query locally, and asks the model to explain the result
in concise language.

The included account data is entirely fictional and uses the reserved
`example.test` email domain.

## Setup on Windows PowerShell

Python 3.13 is supported.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:OPENAI_API_KEY="your-api-key"
```

The API key is read from the environment and is never written to a project
configuration file. You can optionally choose another compatible model:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
```

## Run the app

Create the database and verify the sample data without making an API call:

```powershell
py db_bot.py --reset-db --init-only
```

Start the interactive CLI:

```powershell
py db_bot.py
```

Ask one question:

```powershell
py db_bot.py --question "Which player has the most total kills?"
```

Run all six sample questions and save their results:

```powershell
py db_bot.py --demo
```

Every attempted question is written as JSON under `responses/`. Logs contain
the question, generated SQL, query rows, friendly answer, selected model, and
any error. They never contain the API key.

## Normalization changes

The original schema mixed entities with relationship tables and gave several
relationships a single-column primary key. That would allow only one team per
game, one player per team, or one game per player. The corrected schema uses:

- `game_instances` as the one authoritative game table; the overlapping
  `games` table was removed.
- `game_teams(game_id, team_id)` for the many-to-many relationship between
  games and teams. A per-game unique constraint ensures one Red and one Blue
  team.
- `team_membership(team_id, player_id, joined_at)` so a team can have multiple
  players and membership history can be retained.
- `player_game_stats(game_id, player_id)` so each player can have statistics
  for every game. Its `(game_id, team_id)` foreign key also ensures that the
  recorded team participated in that game.
- A computed `player_stats` view for lifetime totals. This avoids storing totals
  that could disagree with the individual game rows.
- Composite objective foreign keys so an objective can only be credited to a
  team participating in that same game.

SQLite `CHECK` constraints replace the incomplete enums. Positions use numeric
`position_x` and `position_y` columns, and map/variant values are restricted to
1 through 10.

## Safety boundaries

Model-produced SQL must begin with `SELECT` or `WITH`, may contain only one
statement, and is screened for modifying operations. It then runs through a
separate SQLite connection opened with `mode=ro` and `PRAGMA query_only`, with a
two-second execution limit and a 100-row output limit.

These controls make the classroom demo safer, but they are not a substitute
for database permissions and a dedicated reporting replica in a production
employee tool.

## Project files

- `Competitive_Game_Schema.sql` — normalized SQLite schema
- `setupData.sql` — small fictional demonstration dataset
- `db_bot.py` — CLI, OpenAI calls, SQL validation, execution, and logging
- `test_db_bot.py` — offline database and query-safety tests
- `requirements.txt` — Python dependency list

## Run tests

The tests do not need an API key or network connection.

```powershell
py -m unittest -v
```
