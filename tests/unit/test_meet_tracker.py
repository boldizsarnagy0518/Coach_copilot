"""Unit tests for Meet Tracker tool."""

import pytest
from unittest.mock import patch
import duckdb


@pytest.fixture
def mock_db_connection():
    """Create a temporary in-memory DuckDB connection for testing."""
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_results (
            id INTEGER PRIMARY KEY,
            meet_date DATE NOT NULL,
            meet_name VARCHAR NOT NULL,
            weight_class VARCHAR,
            squat DOUBLE,
            bench DOUBLE,
            deadlift DOUBLE,
            total DOUBLE,
            place INTEGER,
            notes VARCHAR DEFAULT ''
        )
    """)
    return conn


class TestRecordMeetResult:
    """Tests for record_meet_result tool."""

    @patch("src.tools.meet_tracker._get_db_connection")
    def test_record_meet_success(self, mock_get_conn, mock_db_connection):
        """Test successful meet result recording."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.meet_tracker import record_meet_result

        result = record_meet_result.invoke(
            {
                "meet_name": "National Championships 2025",
                "meet_date": "2025-06-15",
                "squat": 200.0,
                "bench": 140.0,
                "deadlift": 240.0,
                "weight_class": "83kg",
                "placing": 1,
            }
        )

        assert "✅ Recorded" in result
        assert "580" in result  # Total
        assert "National Championships" in result

    @patch("src.tools.meet_tracker._get_db_connection")
    def test_record_meet_detects_pr(self, mock_get_conn, mock_db_connection):
        """Test that PR detection works."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.meet_tracker import record_meet_result

        # First meet
        record_meet_result.invoke(
            {
                "meet_name": "First Meet",
                "meet_date": "2025-01-01",
                "squat": 180.0,
                "bench": 120.0,
                "deadlift": 220.0,
            }
        )

        # Second meet with PR
        result = record_meet_result.invoke(
            {
                "meet_name": "Second Meet",
                "meet_date": "2025-06-01",
                "squat": 200.0,
                "bench": 140.0,
                "deadlift": 240.0,
            }
        )

        assert "PR!" in result or "over previous best" in result


class TestGetPRHistory:
    """Tests for get_pr_history tool."""

    @patch("src.tools.meet_tracker._get_db_connection")
    def test_pr_history_empty(self, mock_get_conn, mock_db_connection):
        """Test PR history with no meets."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.meet_tracker import get_pr_history

        result = get_pr_history.invoke({})

        assert "No competition results" in result

    @patch("src.tools.meet_tracker._get_db_connection")
    def test_pr_history_with_data(self, mock_get_conn, mock_db_connection):
        """Test PR history with existing meets."""
        mock_get_conn.return_value = mock_db_connection

        # Insert test data
        mock_db_connection.execute(
            """INSERT INTO meet_results 
               (meet_date, meet_name, squat, bench, deadlift, total) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            ["2025-01-15", "Test Meet", 200.0, 140.0, 240.0, 580.0],
        )

        from src.tools.meet_tracker import get_pr_history

        result = get_pr_history.invoke({})

        assert "PR History" in result or "Test Meet" in result

    @patch("src.tools.meet_tracker._get_db_connection")
    def test_pr_calculation_correct(self, mock_get_conn, mock_db_connection):
        """Test that PRs are calculated correctly over time."""
        mock_get_conn.return_value = mock_db_connection

        # First meet
        mock_db_connection.execute(
            """INSERT INTO meet_results 
               (meet_date, meet_name, squat, bench, deadlift, total) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            ["2025-01-01", "Meet 1", 180.0, 120.0, 200.0, 500.0],
        )

        # Second meet (improvement)
        mock_db_connection.execute(
            """INSERT INTO meet_results 
               (meet_date, meet_name, squat, bench, deadlift, total) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            ["2025-06-01", "Meet 2", 200.0, 130.0, 220.0, 550.0],
        )

        from src.tools.meet_tracker import get_pr_history

        result = get_pr_history.invoke({})

        # Should show the all-time PRs
        assert "200" in result  # Squat PR
        assert "550" in result  # Total PR


class TestCompareToCompetition:
    """Tests for compare_to_competition tool."""

    @patch("src.tools.meet_tracker._get_db_connection")
    def test_compare_no_meets(self, mock_get_conn, mock_db_connection):
        """Test comparison when no meets exist."""
        mock_get_conn.return_value = mock_db_connection

        from src.tools.meet_tracker import compare_to_competition

        result = compare_to_competition.invoke({})

        assert "No competition results found" in result

    @patch("src.tools.meet_tracker._get_db_connection")
    def test_compare_returns_latest(self, mock_get_conn, mock_db_connection):
        """Test that comparison returns latest meet by default."""
        mock_get_conn.return_value = mock_db_connection

        # Insert two meets
        mock_db_connection.execute(
            """INSERT INTO meet_results 
               (meet_date, meet_name, squat, bench, deadlift, total, weight_class) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ["2025-01-01", "Old Meet", 180.0, 120.0, 200.0, 500.0, "83kg"],
        )
        mock_db_connection.execute(
            """INSERT INTO meet_results 
               (meet_date, meet_name, squat, bench, deadlift, total, weight_class) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ["2025-06-01", "Recent Meet", 200.0, 140.0, 240.0, 580.0, "83kg"],
        )

        from src.tools.meet_tracker import compare_to_competition

        result = compare_to_competition.invoke({})

        assert "Recent Meet" in result
        assert "580" in result
