from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.user_profile import UserProfile
from ..schemas.user_profile import UserProfileResponse, UserProfileUpdate
from ..services.cache_service import cache_service

router = APIRouter(prefix="/users/cached", tags=["users-cached"])
logger = logging.getLogger(__name__)

@router.get("/profile/me", response_model=UserProfileResponse)
async def get_my_cached_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile with caching"""
    # Try cache first
    cached_profile = cache_service.get_user_profile(str(current_user.id))
    if cached_profile:
        logger.info(f"Cache hit for user profile: {current_user.id}")
        return cached_profile
    
    # Cache miss - fetch from database
    logger.info(f"Cache miss for user profile: {current_user.id}")
    
    # Check if this is the development mock user
    if str(current_user.id) == "00000000-0000-0000-0000-000000000001":
        # Return mock profile for development
        profile_data = {
            "user_id": str(current_user.id),
            "display_name": "Dev User",
            "avatar_url": "https://via.placeholder.com/150",
            "hero_class": "Warrior",
            "level": 5,
            "experience": 2500,
            "rank": "C",
            "hp": 100,
            "mp": 50,
            "power": 15,
            "wisdom": 12,
            "speed": 10,
            "orbs": 1500,
            "crystals": 25,
            "premium_status": "free",
            "premium_until": None,
            "streak_days": 3,
            "last_login": datetime.utcnow(),
            "achievements_count": 8,
            "battles_won": 18,
            "battles_lost": 7,
            "questions_answered": 95,
            "correct_answers": 67,
            "guild_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        # Cache the mock profile
        cache_service.cache_user_profile(str(current_user.id), profile_data, ttl=3600)
        return profile_data
    
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        # En lugar de 404, devolver perfil básico
        profile_data = {
            "user_id": str(current_user.id),
            "display_name": getattr(current_user, "display_name", current_user.username),
            "avatar_url": None,
            "hero_class": "Warrior",
            "level": 1,
            "experience": 0,
            "rank": "F",
            "hp": 100,
            "mp": 50,
            "power": 10,
            "wisdom": 10,
            "speed": 10,
            "orbs": 1000,
            "crystals": 10,
            "premium_status": "free",
            "premium_until": None,
            "streak_days": 0,
            "last_login": datetime.utcnow(),
            "achievements_count": 0,
            "battles_won": 0,
            "battles_lost": 0,
            "questions_answered": 0,
            "correct_answers": 0,
            "guild_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    else:
        # Build response from existing profile
        profile_data = {
            "user_id": str(profile.user_id),
            "display_name": profile.display_name,
            "avatar_url": profile.avatar_url,
            "hero_class": profile.hero_class,
            "level": profile.level,
            "experience": profile.experience,
            "rank": profile.rank,
            "hp": profile.hp,
            "mp": profile.mp,
            "power": profile.power,
            "wisdom": profile.wisdom,
            "speed": profile.speed,
            "orbs": profile.orbs,
            "crystals": profile.crystals,
            "premium_status": profile.premium_status,
            "premium_until": profile.premium_until,
            "streak_days": profile.streak_days,
            "last_login": profile.last_login,
            "achievements_count": profile.achievements_count,
            "battles_won": profile.battles_won,
            "battles_lost": profile.battles_lost,
            "questions_answered": profile.questions_answered,
            "correct_answers": profile.correct_answers,
            "guild_id": str(profile.guild_id) if profile.guild_id else None,
            "created_at": profile.created_at,
        "updated_at": profile.updated_at
    }
    
    # Cache the profile
    cache_service.cache_user_profile(str(current_user.id), profile_data, ttl=3600)
    
    return profile_data

@router.put("/profile/me", response_model=UserProfileResponse)
async def update_my_cached_profile(
    profile_update: UserProfileUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile and invalidate cache"""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Update fields
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    # Invalidate cache
    cache_service.invalidate_user_profile(str(current_user.id))
    
    # Update cache in background
    profile_data = {
        "user_id": str(profile.user_id),
        "display_name": profile.display_name,
        "avatar_url": profile.avatar_url,
        "hero_class": profile.hero_class,
        "level": profile.level,
        "experience": profile.experience,
        "rank": profile.rank,
        "hp": profile.hp,
        "mp": profile.mp,
        "power": profile.power,
        "wisdom": profile.wisdom,
        "speed": profile.speed,
        "orbs": profile.orbs,
        "crystals": profile.crystals,
        "premium_status": profile.premium_status,
        "premium_until": profile.premium_until,
        "streak_days": profile.streak_days,
        "last_login": profile.last_login,
        "achievements_count": profile.achievements_count,
        "battles_won": profile.battles_won,
        "battles_lost": profile.battles_lost,
        "questions_answered": profile.questions_answered,
        "correct_answers": profile.correct_answers,
        "guild_id": str(profile.guild_id) if profile.guild_id else None,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at
    }
    
    background_tasks.add_task(
        cache_service.cache_user_profile,
        str(current_user.id),
        profile_data
    )
    
    return profile_data

@router.post("/profile/level-up")
async def level_up_with_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Level up user and update cache"""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Calculate experience needed for next level
    exp_needed = profile.level * 100
    
    if profile.experience < exp_needed:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough experience. Need {exp_needed}, have {profile.experience}"
        )
    
    # Level up
    profile.level += 1
    profile.experience -= exp_needed
    
    # Increase stats
    profile.hp += 10
    profile.mp += 5
    profile.power += 2
    profile.wisdom += 2
    profile.speed += 1
    
    # Check for rank up
    if profile.level >= 20 and profile.rank == "E":
        profile.rank = "D"
    elif profile.level >= 40 and profile.rank == "D":
        profile.rank = "C"
    elif profile.level >= 60 and profile.rank == "C":
        profile.rank = "B"
    elif profile.level >= 80 and profile.rank == "B":
        profile.rank = "A"
    elif profile.level >= 100 and profile.rank == "A":
        profile.rank = "S"
    
    db.commit()
    
    # Invalidate and update cache
    cache_service.invalidate_user_profile(str(current_user.id))
    
    return {
        "message": "Level up successful!",
        "new_level": profile.level,
        "new_rank": profile.rank,
        "stats_increased": {
            "hp": 10,
            "mp": 5,
            "power": 2,
            "wisdom": 2,
            "speed": 1
        }
    }

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_cached_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get any user's profile with caching"""
    # Try cache first
    cached_profile = cache_service.get_user_profile(user_id)
    if cached_profile:
        logger.info(f"Cache hit for user profile: {user_id}")
        return cached_profile
    
    # Cache miss - fetch from database
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Build response
    profile_data = {
        "user_id": str(profile.user_id),
        "display_name": profile.display_name,
        "avatar_url": profile.avatar_url,
        "hero_class": profile.hero_class,
        "level": profile.level,
        "experience": profile.experience,
        "rank": profile.rank,
        "hp": profile.hp,
        "mp": profile.mp,
        "power": profile.power,
        "wisdom": profile.wisdom,
        "speed": profile.speed,
        "orbs": profile.orbs,
        "crystals": profile.crystals,
        "premium_status": profile.premium_status,
        "premium_until": profile.premium_until,
        "streak_days": profile.streak_days,
        "last_login": profile.last_login,
        "achievements_count": profile.achievements_count,
        "battles_won": profile.battles_won,
        "battles_lost": profile.battles_lost,
        "questions_answered": profile.questions_answered,
        "correct_answers": profile.correct_answers,
        "guild_id": str(profile.guild_id) if profile.guild_id else None,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at
    }
    
    # Cache the profile
    cache_service.cache_user_profile(user_id, profile_data, ttl=3600)
    
    return profile_data

@router.post("/cache/invalidate-all")
async def invalidate_all_user_cache(
    current_user: User = Depends(get_current_user)
):
    """Invalidate all user cache (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    deleted = cache_service.delete_pattern("user:profile:*")
    
    return {
        "message": f"Invalidated {deleted} user profile cache entries"
    }

@router.get("/cache/stats")
async def get_user_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """Get user cache statistics (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    profile_keys = cache_service.get_keys("user:profile:*")
    
    return {
        "total_cached_profiles": len(profile_keys),
        "sample_keys": profile_keys[:10],
        "cache_health": cache_service.ping()
    }