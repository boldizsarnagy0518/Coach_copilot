"""RPE Logger tool with DuckDB persistence."""

from pydantic import BaseModel, Field
from langchain_core.tools import tool
import duckdb

from src.config import settings


def _get_db_connection():
    """Get DuckDB connection and ensure tables exist."""
    conn = duckdb.connect(str(settings.duckdb_path))

    # Create RPE logs table if not exists
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
    return conn


class RPELogInput(BaseModel):
    """Input schema for RPE logging."""

    exercise: str = Field(description="Exercise name (squat, bench, deadlift)")
    weight: float = Field(description="Weight in kg")
    reps: int = Field(description="Number of reps")
    rpe: float = Field(ge=1, le=10, description="RPE scale 1-10")
    notes: str = Field(default="", description="Optional notes")


@tool(args_schema=RPELogInput)
def log_rpe(
    exercise: str, weight: float, reps: int, rpe: float, notes: str = ""
) -> str:
    """
    Log Rate of Perceived Exertion (RPE) for a set.

    Use this tool when the user wants to log or record their RPE for a workout set.
    The RPE scale goes from 1 (very easy) to 10 (maximum effort/failure).

    Args:
        exercise: Exercise name (e.g., "squat", "bench press", "deadlift")
        weight: Weight used in kg
        reps: Number of repetitions performed
        rpe: Rate of Perceived Exertion (1-10 scale)
        notes: Optional notes about the set

    Returns:
        Confirmation message with weekly RPE average for the exercise
    """
    try:
        # Validate RPE range
        if not 1 <= rpe <= 10:
            return f"Error: RPE must be between 1 and 10. You provided: {rpe}"

        conn = _get_db_connection()

        # Insert the log
        conn.execute(
            """
            INSERT INTO rpe_logs (exercise, weight, reps, rpe, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            [exercise.lower(), weight, reps, rpe, notes],
        )

        # Get weekly average for this exercise
        result = conn.execute(
            """
            SELECT AVG(rpe) as avg_rpe, COUNT(*) as count
            FROM rpe_logs
            WHERE LOWER(exercise) = LOWER(?)
            AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
            """,
            [exercise],
        ).fetchone()

        conn.close()

        avg_rpe = result[0] if result[0] else rpe
        count = result[1] if result[1] else 1

        return (
            f"✅ Logged: {exercise} {weight}kg x {reps} @ RPE {rpe}\n"
            f"📊 Weekly average RPE for {exercise}: {avg_rpe:.1f} ({count} sets)"
        )

    except Exception as e:
        return f"Error logging RPE: {str(e)}"


@tool
def get_rpe_history(exercise: str = "", days: int = 7) -> str:
    """
    Get RPE history for an exercise over a time period.

    Args:
        exercise: Exercise name to filter by (empty for all exercises)
        days: Number of days to look back (default: 7)

    Returns:
        RPE history with trends
    """
    try:
        conn = _get_db_connection()

        if exercise:
            result = conn.execute(
                """
                SELECT timestamp, exercise, weight, reps, rpe, notes
                FROM rpe_logs
                WHERE LOWER(exercise) = LOWER(?)
                AND timestamp >= CURRENT_TIMESTAMP - INTERVAL ? DAY
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                [exercise, days],
            ).fetchall()
        else:
            result = conn.execute(
                """
                SELECT timestamp, exercise, weight, reps, rpe, notes
                FROM rpe_logs
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL ? DAY
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                [days],
            ).fetchall()

        conn.close()

        if not result:
            return f"No RPE logs found for the last {days} days."

        lines = [f"📊 RPE History (last {days} days):\n"]
        for row in result:
            ts, ex, wt, reps, rpe, notes = row
            date_str = ts.strftime("%m/%d") if hasattr(ts, "strftime") else str(ts)[:10]
            line = f"  {date_str}: {ex.title()} {wt}kg x {reps} @ RPE {rpe}"
            if notes:
                line += f" ({notes})"
            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        return f"Error retrieving RPE history: {str(e)}"


ALL_TOOLS = [log_rpe, get_rpe_history]
