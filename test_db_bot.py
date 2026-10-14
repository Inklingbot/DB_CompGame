import sqlite3
import unittest
from pathlib import Path

import db_bot


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = Path(db_bot.APP_DIR) / ".test_competitive_game.sqlite3"
        db_bot.initialize_database(self.db_path, reset=True)

    def tearDown(self) -> None:
        self.db_path.unlink(missing_ok=True)

    def test_seed_data_and_foreign_keys_are_valid(self) -> None:
        connection = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0], 4)
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM player_identifiers").fetchone()[0],
                8,
            )
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            connection.close()

    def test_player_stats_view_computes_totals(self) -> None:
        columns, rows, truncated = db_bot.run_read_only_query(
            """
            SELECT p.username, s.total_kills, s.total_games
            FROM player_stats AS s
            JOIN player_identifiers AS p USING (player_id)
            ORDER BY s.total_kills DESC
            LIMIT 1
            """,
            self.db_path,
        )
        self.assertEqual(columns, ["username", "total_kills", "total_games"])
        self.assertEqual(rows, [["MayaC", 22, 2]])
        self.assertFalse(truncated)

    def test_read_only_query_can_use_cte(self) -> None:
        _, rows, _ = db_bot.run_read_only_query(
            "WITH active AS (SELECT * FROM objectives WHERE active = 1) "
            "SELECT COUNT(*) FROM active",
            self.db_path,
        )
        self.assertEqual(rows, [[2]])

    def test_rejects_modifying_statement(self) -> None:
        with self.assertRaises(db_bot.QueryRejected):
            db_bot.run_read_only_query("DELETE FROM teams", self.db_path)

    def test_rejects_multiple_statements(self) -> None:
        with self.assertRaises(db_bot.QueryRejected):
            db_bot.run_read_only_query(
                "SELECT * FROM teams; DROP TABLE teams;", self.db_path
            )

    def test_database_is_unchanged_after_rejected_query(self) -> None:
        with self.assertRaises(db_bot.QueryRejected):
            db_bot.run_read_only_query("UPDATE teams SET team = 'Changed'", self.db_path)
        _, rows, _ = db_bot.run_read_only_query(
            "SELECT team FROM teams WHERE id = 1", self.db_path
        )
        self.assertEqual(rows, [["Wasatch Wardens"]])


if __name__ == "__main__":
    unittest.main()
