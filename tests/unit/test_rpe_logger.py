"""Unit tests for RPE Logger tool."""

import pytest
from unittest.mock import patch
import duckdb


@pytest.fixture
def mock_db_connection():
    """Create a temporary in-memory DuckDB connection for testing."""
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rpe_logs (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exercise VARCHAR NOT NULL,
            weight DOUBLE NOT NULL,
            reps INTEGER NOT NULL,
            rpe DOUBLE NOT NULL,
            notes VARCHAR DEFAULT ''
        )
    """)
    return conn


class TestLogRPE:
    """Tests for log_rpe tool."""

    @patch("src.tools.rpe_logger._get_db_connection")
    def test_log_rpe_success(self, mock_get_conn, mock_db_connection):
        """Test successful RPE logging."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.rpe_logger import log_rpe

        result = log_rpe.invoke(
            {
                "exercise": "squat",
                "weight": 140.0,
                "reps": 5,
                "rpe": 8.0,
                "notes": "Felt good",
            }
        )

        assert "✅ Logged" in result
        assert "squat" in result
        assert "140" in result
        assert "RPE 8" in result

    @patch("src.tools.rpe_logger._get_db_connection")
    def test_log_rpe_validation_error(self, mock_get_conn, mock_db_connection):
        """Test RPE validation (must be 1-10)."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.rpe_logger import log_rpe

        # RPE of 11 should fail
        result = log_rpe.invoke(
            {"exercise": "bench", "weight": 100.0, "reps": 3, "rpe": 11.0}
        )

        assert "Error" in result or "must be between" in result

    @patch("src.tools.rpe_logger._get_db_connection")
    def test_log_rpe_returns_weekly_average(self, mock_get_conn, mock_db_connection):
        """Test that logging returns weekly average."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.rpe_logger import log_rpe

        # Log first entry
        log_rpe.invoke({"exercise": "deadlift", "weight": 180.0, "reps": 3, "rpe": 7.0})

        # Log second entry
        result = log_rpe.invoke(
            {"exercise": "deadlift", "weight": 190.0, "reps": 2, "rpe": 9.0}
        )

        assert "Weekly average" in result or "avg" in result.lower()


class TestGetRPEHistory:
    """Tests for get_rpe_history tool."""

    @patch("src.tools.rpe_logger._get_db_connection")
    def test_get_history_empty(self, mock_get_conn, mock_db_connection):
        """Test history with no logs."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.rpe_logger import get_rpe_history

        result = get_rpe_history.invoke({"days": 7})

        assert "No RPE logs found" in result

    @patch("src.tools.rpe_logger._get_db_connection")
    def test_get_history_with_data(self, mock_get_conn, mock_db_connection):
        """Test history with existing logs."""
        mock_get_conn.return_value = mock_db_connection

        # Insert test data
        mock_db_connection.execute(
            "INSERT INTO rpe_logs (exercise, weight, reps, rpe) VALUES (?, ?, ?, ?)",
            ["squat", 140.0, 5, 8.0],
        )

        from src.tools.rpe_logger import get_rpe_history

        result = get_rpe_history.invoke({"days": 7})

        assert "RPE History" in result or "squat" in result.lower()
