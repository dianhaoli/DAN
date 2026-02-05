"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('firebase_uid', sa.String(128), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('photo_url', sa.Text, nullable=True),
        sa.Column('username', sa.String(50), unique=True, nullable=True, index=True),
        sa.Column('xp', sa.Integer, default=0, nullable=False),
        sa.Column('level', sa.Integer, default=0, nullable=False),
        sa.Column('streak', sa.Integer, default=0, nullable=False),
        sa.Column('longest_streak', sa.Integer, default=0, nullable=False),
        sa.Column('total_study_time', sa.Integer, default=0, nullable=False),
        sa.Column('weekly_goal', sa.Integer, nullable=True),
        sa.Column('preferred_study_time', sa.String(50), nullable=True),
        sa.Column('is_public', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=True),
        sa.Column('duration', sa.Integer, nullable=False),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('domains', postgresql.ARRAY(sa.Text), default=[], nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('tab_switches', sa.Integer, default=0, nullable=False),
        sa.Column('active_time', sa.Integer, default=0, nullable=False),
        sa.Column('idle_time', sa.Integer, default=0, nullable=False),
        sa.Column('clicks', sa.Integer, nullable=True),
        sa.Column('keystrokes', sa.Integer, nullable=True),
        sa.Column('focus_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('productivity_score', sa.Integer, nullable=True),
        sa.Column('activity_label', sa.String(50), nullable=True),
        sa.Column('processing_status', sa.String(20), default='pending', nullable=False),
        sa.Column('ml_model_version', sa.String(100), nullable=True),
        sa.Column('ml_features', postgresql.JSONB, nullable=True),
        sa.Column('ml_processed_at', sa.DateTime, nullable=True),
        sa.Column('source', sa.String(50), default='extension', nullable=False),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('ai_summary', sa.Text, nullable=True),
        sa.Column('topics', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('xp_earned', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Todos table
    op.create_table(
        'todos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('estimated_minutes', sa.Integer, nullable=True),
        sa.Column('actual_minutes', sa.Integer, nullable=True),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('scheduled_date', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('linked_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('priority', sa.String(20), default='medium', nullable=False),
        sa.Column('xp_reward', sa.Integer, default=10, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Friends junction table (replaces UUID[] array)
    op.create_table(
        'friends',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('friend_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # Friend requests table
    op.create_table(
        'friend_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('from_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('to_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('from_user_id', 'to_user_id', name='uq_friend_request'),
    )

    # Activities table
    op.create_table(
        'activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_name', sa.String(255), nullable=False),
        sa.Column('user_photo', sa.Text, nullable=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic', sa.String(255), nullable=True),
        sa.Column('duration', sa.Integer, nullable=True),
        sa.Column('xp_earned', sa.Integer, nullable=True),
        sa.Column('badge_id', sa.String(50), nullable=True),
        sa.Column('badge_name', sa.String(100), nullable=True),
        sa.Column('new_level', sa.Integer, nullable=True),
        sa.Column('streak_days', sa.Integer, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True),
        sa.Column('reactions', postgresql.JSONB, default={}, nullable=False),
    )

    # User stats table (derived data, updated by background jobs)
    op.create_table(
        'user_stats',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('total_sessions', sa.Integer, default=0, nullable=False),
        sa.Column('total_hours', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('average_focus_score', sa.Numeric(3, 2), default=0, nullable=False),
        sa.Column('average_productivity_score', sa.Integer, default=0, nullable=False),
        sa.Column('topic_distribution', postgresql.JSONB, default={}, nullable=False),
        sa.Column('study_heatmap', postgresql.JSONB, default={}, nullable=False),
        sa.Column('weekly_trend', postgresql.JSONB, default=[], nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # User quotas table (rate limiting)
    op.create_table(
        'user_quotas',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('ai_requests_today', sa.Integer, default=0, nullable=False),
        sa.Column('ai_requests_reset_at', sa.DateTime, nullable=True),
        sa.Column('last_request_at', sa.DateTime, nullable=True),
    )

    # Badges table
    op.create_table(
        'badges',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('icon', sa.String(100), nullable=False),
        sa.Column('requirement', sa.Text, nullable=False),
        sa.Column('rarity', sa.String(20), nullable=False),
    )

    # User badges table
    op.create_table(
        'user_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('badge_id', sa.String(50), sa.ForeignKey('badges.id'), nullable=False),
        sa.Column('earned_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )

    # Leaderboards table (cached data)
    op.create_table(
        'leaderboards',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('scope', sa.String(20), nullable=False),
        sa.Column('entries', postgresql.JSONB, default=[], nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Weekly summaries table
    op.create_table(
        'weekly_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('week_start', sa.DateTime, nullable=False),
        sa.Column('week_end', sa.DateTime, nullable=False),
        sa.Column('total_hours', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_sessions', sa.Integer, nullable=False),
        sa.Column('average_focus_score', sa.Numeric(3, 2), nullable=False),
        sa.Column('average_productivity_score', sa.Integer, nullable=False),
        sa.Column('xp_earned', sa.Integer, nullable=False),
        sa.Column('new_badges', postgresql.ARRAY(sa.Text), default=[], nullable=False),
        sa.Column('streak_at_end', sa.Integer, nullable=False),
        sa.Column('top_topics', postgresql.JSONB, default=[], nullable=False),
        sa.Column('ai_summary', sa.Text, nullable=True),
        sa.Column('improvements', postgresql.ARRAY(sa.Text), default=[], nullable=False),
        sa.Column('suggestions', postgresql.ARRAY(sa.Text), default=[], nullable=False),
        sa.Column('ai_model', sa.String(50), nullable=True),
        sa.Column('ai_prompt_hash', sa.String(64), nullable=True),
        sa.Column('regenerated_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # AI cache table
    op.create_table(
        'ai_cache',
        sa.Column('prompt_hash', sa.String(64), primary_key=True),
        sa.Column('model', sa.String(50), nullable=False),
        sa.Column('response', sa.Text, nullable=False),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_table('ai_cache')
    op.drop_table('weekly_summaries')
    op.drop_table('leaderboards')
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('user_quotas')
    op.drop_table('user_stats')
    op.drop_table('activities')
    op.drop_table('friend_requests')
    op.drop_table('friends')
    op.drop_table('todos')
    op.drop_table('sessions')
    op.drop_table('users')
