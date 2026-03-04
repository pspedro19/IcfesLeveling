# Routes package - all routers registered directly in main.py
# This file exports route modules for convenience

from . import (
    # TIER 1: ESSENTIAL
    auth,
    questions,
    hearts,
    streak,
    mobile_api,

    # TIER 2: GAMIFICATION
    economy,
    achievements,
    leaderboard,
    notifications,
    quests,
    answers,
    battles,
    practice,

    # TIER 3: DIAGNOSTIC
    diagnostic_public,
    diagnostic_two_phase,
    monthly_reassessment,
    verified_image_diagnostic,

    # TIER 4: STUDY PLANS
    study_plans,
    quizzes,
    spaced_repetition,

    # TIER 5: VIDEO & CONTENT
    videos,
    video_recommendations,

    # TIER 6: SOCIAL & COMPETITIVE
    guilds,
    leagues,
    store,
    boss_raid,
    bosses,
    premium_simple,
    dungeons,

    # TIER 7: AI & ASSETS
    ai,
    ai_tips,
    images,

    # TIER 8: ANALYTICS
    mastery,

    # TIER 9: ONBOARDING
    onboarding,
)
