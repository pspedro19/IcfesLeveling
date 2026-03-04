"""Add performance indexes for hot queries

Revision ID: perf_indexes_001
Revises: None
Create Date: 2026-02-18 12:00:00

Indexes added:
- idx_practice_user_created: practice_sessions(user_id, created_at)
- idx_questions_subject_difficulty: questions(subject_id, difficulty_level)
- idx_user_engagement_streak: user_engagement(current_streak, today_xp)
- idx_daily_activity_user_date: user_daily_activity(user_id, activity_date)
- idx_leaderboard_type_score: leaderboard(leaderboard_type, score DESC)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'perf_indexes_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Practice sessions - frequent query by user + time range
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_practice_user_created
        ON practice_sessions (user_id, created_at DESC);
    """)

    # Questions - filtered by subject and difficulty in practice mode
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_questions_subject_difficulty
        ON questions (subject_id, difficulty_level);
    """)

    # User engagement - streak queries (daily reset, reminders)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_engagement_streak
        ON user_engagement (current_streak, today_xp);
    """)

    # Daily activity - lookup by user + date
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_daily_activity_user_date
        ON user_daily_activity (user_id, activity_date DESC);
    """)

    # Leaderboard - sorted queries by type and score
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_leaderboard_type_score
        ON leaderboard (leaderboard_type, score DESC);
    """)

    # User question history - anti-gaming detection queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_question_history_user_created
        ON user_question_history (user_id, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_practice_user_created;")
    op.execute("DROP INDEX IF EXISTS idx_questions_subject_difficulty;")
    op.execute("DROP INDEX IF EXISTS idx_user_engagement_streak;")
    op.execute("DROP INDEX IF EXISTS idx_daily_activity_user_date;")
    op.execute("DROP INDEX IF EXISTS idx_leaderboard_type_score;")
    op.execute("DROP INDEX IF EXISTS idx_question_history_user_created;")
