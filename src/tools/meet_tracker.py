"""Meet Results Tracker with DuckDB persistence."""

from pydantic import BaseModel, Field
from langchain_core.tools import tool
import duckdb

from src.config import settings


def _get_db_connection():
    """Get DuckDB connection and ensure tables exist."""
    conn = duckdb.connect(str(settings.duckdb_path))

    # Create meet results table if not exists
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
    return conn


class MeetResultInput(BaseModel):
    """Input schema for recording meet results."""

    meet_name: str = Field(description="Competition name")
    meet_date: str = Field(description="Competition date (YYYY-MM-DD)")
    squat: float = Field(description="Best squat in kg")
    bench: float = Field(description="Best bench press in kg")
    deadlift: float = Field(description="Best deadlift in kg")
    weight_class: str = Field(
        default="", description="Weight class (e.g., '83kg', '93kg')"
    )
    placing: int = Field(default=0, description="Placing in competition (0 if unknown)")
    notes: str = Field(default="", description="Optional notes")


@tool(args_schema=MeetResultInput)
def record_meet_result(
    meet_name: str,
    meet_date: str,
    squat: float,
    bench: float,
    deadlift: float,
    weight_class: str = "",
    placing: int = 0,
    notes: str = "",
) -> str:
    """
    Record a competition/meet result.

    Use this tool when the user wants to log their powerlifting competition results.

    Args:
        meet_name: Name of the competition
        meet_date: Date of competition (YYYY-MM-DD format)
        squat: Best squat achieved in kg
        bench: Best bench press achieved in kg
        deadlift: Best deadlift achieved in kg
        weight_class: Weight class competed in
        placing: Final placing (0 if unknown)
        notes: Any additional notes

    Returns:
        Confirmation with total and comparison to previous meets
    """
    try:
        total = squat + bench + deadlift

        conn = _get_db_connection()

        # Insert the result
        conn.execute(
            """
            INSERT INTO meet_results (meet_date, meet_name, weight_class, squat, bench, deadlift, total, place, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                meet_date,
                meet_name,
                weight_class,
                squat,
                bench,
                deadlift,
                total,
                placing,
                notes,
            ],
        )

        # Get previous best total for comparison (exclude current by using second-highest)
        prev_best = conn.execute(
            """
            SELECT MAX(total) as best_total
            FROM meet_results
            WHERE total < ?
            """,
            [total],
        ).fetchone()

        conn.close()

        result_msg = (
            f"✅ Recorded: {meet_name} ({meet_date})\n"
            f"  Squat: {squat}kg | Bench: {bench}kg | Deadlift: {deadlift}kg\n"
            f"  Total: {total}kg"
        )

        if weight_class:
            result_msg += f" @ {weight_class}"
        if placing > 0:
            result_msg += f" | Placing: {placing}"

        if prev_best and prev_best[0]:
            diff = total - prev_best[0]
            if diff > 0:
                result_msg += f"\n🎉 PR! +{diff}kg over previous best!"
            elif diff < 0:
                result_msg += f"\n📉 {abs(diff)}kg below previous best"

        return result_msg

    except Exception as e:
        return f"Error recording meet result: {str(e)}"


@tool
def get_pr_history(lift: str = "") -> str:
    """
    Get personal record (PR) history for competition lifts.

    Args:
        lift: Specific lift to check ("squat", "bench", "deadlift", or empty for all)

    Returns:
        PR progression over time
    """
    try:
        conn = _get_db_connection()

        result = conn.execute(
            """
            SELECT meet_date, meet_name, squat, bench, deadlift, total
            FROM meet_results
            ORDER BY meet_date ASC
            """
        ).fetchall()

        conn.close()

        if not result:
            return "No competition results recorded yet."

        lines = ["📊 Competition PR History:\n"]

        # Track running PRs
        pr_squat = pr_bench = pr_deadlift = pr_total = 0

        for row in result:
            date, name, sq, bn, dl, total = row
            date_str = str(date)[:10] if date else "Unknown"

            prs_hit = []
            if sq and sq > pr_squat:
                pr_squat = sq
                prs_hit.append(f"Squat {sq}kg")
            if bn and bn > pr_bench:
                pr_bench = bn
                prs_hit.append(f"Bench {bn}kg")
            if dl and dl > pr_deadlift:
                pr_deadlift = dl
                prs_hit.append(f"Deadlift {dl}kg")
            if total and total > pr_total:
                pr_total = total
                prs_hit.append(f"Total {total}kg")

            if prs_hit or not lift:
                lines.append(f"  {date_str} - {name}")
                if prs_hit:
                    lines.append(f"    🏆 PRs: {', '.join(prs_hit)}")

        lines.append("\n📈 Current All-Time PRs:")
        lines.append(
            f"  Squat: {pr_squat}kg | Bench: {pr_bench}kg | Deadlift: {pr_deadlift}kg | Total: {pr_total}kg"
        )

        return "\n".join(lines)

    except Exception as e:
        return f"Error retrieving PR history: {str(e)}"


@tool
def compare_to_competition(meet_name: str = "") -> str:
    """
    Compare current training to competition results.

    Args:
        meet_name: Specific meet to compare against (empty for most recent)

    Returns:
        Comparison of training vs competition performance
    """
    try:
        conn = _get_db_connection()

        if meet_name:
            result = conn.execute(
                """
                SELECT meet_date, meet_name, squat, bench, deadlift, total, weight_class, place
                FROM meet_results
                WHERE LOWER(meet_name) LIKE LOWER(?)
                ORDER BY meet_date DESC
                LIMIT 1
                """,
                [f"%{meet_name}%"],
            ).fetchone()
        else:
            result = conn.execute(
                """
                SELECT meet_date, meet_name, squat, bench, deadlift, total, weight_class, place
                FROM meet_results
                ORDER BY meet_date DESC
                LIMIT 1
                """
            ).fetchone()

        conn.close()

        if not result:
            return "No competition results found for comparison."

        date, name, sq, bn, dl, total, wc, placing = result

        lines = [
            f"📋 Last Competition: {name} ({str(date)[:10]})",
            f"  Weight Class: {wc or 'Unknown'}",
            f"  Results: Squat {sq}kg | Bench {bn}kg | Deadlift {dl}kg",
            f"  Total: {total}kg" + (f" | Place: {placing}" if placing else ""),
            "",
            "💡 To compare with training, check your RPE history with get_rpe_history()",
        ]

        return "\n".join(lines)

    except Exception as e:
        return f"Error comparing to competition: {str(e)}"


ALL_TOOLS = [record_meet_result, get_pr_history, compare_to_competition]
