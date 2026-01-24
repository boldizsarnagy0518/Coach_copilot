"""Seed data for DuckDB athlete database.

Run this script to populate the database with sample data for testing.
Usage: uv run python -m src.utils.seed_data
"""

import duckdb
from datetime import datetime, timedelta
from src.config import settings


def seed_database():
    """Populate the database with sample training and competition data."""
    conn = duckdb.connect(str(settings.duckdb_path))

    # Create tables if they don't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rpe_logs (
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exercise VARCHAR NOT NULL,
            weight DOUBLE NOT NULL,
            reps INTEGER NOT NULL,
            rpe DOUBLE NOT NULL,
            notes VARCHAR DEFAULT ''
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_results (
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

    # Check if we already have data
    rpe_count = conn.execute("SELECT COUNT(*) FROM rpe_logs").fetchone()[0]
    meet_count = conn.execute("SELECT COUNT(*) FROM meet_results").fetchone()[0]

    if rpe_count > 0 or meet_count > 0:
        print(
            f"Database already has data (RPE: {rpe_count}, Meets: {meet_count}). Skipping seed."
        )
        conn.close()
        return

    print("Seeding database with sample data...")

    # ==================== RPE LOGS ====================
    # Simulated training week
    now = datetime.now()

    rpe_data = [
        # Monday - Squat Day
        (now - timedelta(days=6), "squat", 140.0, 5, 7.0, "Warm-up set"),
        (now - timedelta(days=6), "squat", 160.0, 3, 8.0, "Working set 1"),
        (now - timedelta(days=6), "squat", 170.0, 2, 8.5, "Working set 2"),
        (now - timedelta(days=6), "leg press", 200.0, 10, 7.0, ""),
        # Wednesday - Bench Day
        (now - timedelta(days=4), "bench press", 100.0, 5, 7.0, "Warm-up"),
        (now - timedelta(days=4), "bench press", 115.0, 3, 8.0, "Working set 1"),
        (now - timedelta(days=4), "bench press", 120.0, 2, 8.5, "Paused"),
        (now - timedelta(days=4), "overhead press", 60.0, 8, 7.5, ""),
        # Friday - Deadlift Day
        (now - timedelta(days=2), "deadlift", 180.0, 3, 7.5, "Warm-up"),
        (now - timedelta(days=2), "deadlift", 200.0, 2, 8.5, "Working set 1"),
        (now - timedelta(days=2), "deadlift", 210.0, 1, 9.0, "Top single"),
        (now - timedelta(days=2), "romanian deadlift", 120.0, 8, 7.0, "Accessory"),
        # Today - Light session
        (now, "squat", 120.0, 5, 6.0, "Recovery"),
        (now, "bench press", 90.0, 5, 6.0, "Recovery"),
    ]

    for ts, exercise, weight, reps, rpe, notes in rpe_data:
        conn.execute(
            "INSERT INTO rpe_logs (timestamp, exercise, weight, reps, rpe, notes) VALUES (?, ?, ?, ?, ?, ?)",
            [ts, exercise, weight, reps, rpe, notes],
        )

    print(f"  Added {len(rpe_data)} RPE log entries")

    # ==================== MEET RESULTS ====================
    meet_data = [
        # First competition (6 months ago)
        (
            "2025-07-01",
            "Budapest Cup 2025",
            "83kg",
            180.0,
            115.0,
            210.0,
            505.0,
            3,
            "First meet",
        ),
        # Second competition (3 months ago)
        (
            "2025-10-15",
            "Hungarian Nationals 2025",
            "83kg",
            195.0,
            125.0,
            225.0,
            545.0,
            2,
            "PR total!",
        ),
        # Most recent
        (
            "2025-12-01",
            "Winter Classic 2025",
            "83kg",
            200.0,
            130.0,
            235.0,
            565.0,
            1,
            "All PRs! First place!",
        ),
    ]

    for meet_date, name, wc, sq, bn, dl, total, placing, notes in meet_data:
        conn.execute(
            """INSERT INTO meet_results 
               (meet_date, meet_name, weight_class, squat, bench, deadlift, total, place, notes) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [meet_date, name, wc, sq, bn, dl, total, placing, notes],
        )

    print(f"  Added {len(meet_data)} competition results")

    conn.close()
    print("\nDatabase seeded successfully!")
    print(f"   Location: {settings.duckdb_path}")


if __name__ == "__main__":
    seed_database()
