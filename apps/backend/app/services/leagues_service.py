"""
Service for League Management - ICFES Leveling

This service encapsulates the business logic for managing user leagues,
including leaderboards, promotions, relegations, and history.
"""

import logging
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models import (
    User,
    LeagueDivision,
    LeagueWeek,
    LeagueGroup,
    UserLeague,
    UserLeagueHistory,
)

logger = logging.getLogger(__name__)

class LeagueService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_league_status(self, user_id: UUID) -> dict:
        """
        Retrieves the current league status for a user.
        """
        active_week = self.db.query(LeagueWeek).filter(LeagueWeek.is_active == True).first()
        if not active_week:
            raise ValueError("NO_ACTIVE_LEAGUE_WEEK")

        user_league = self.db.query(UserLeague).join(LeagueGroup).filter(
            UserLeague.user_id == user_id,
            LeagueGroup.league_week_id == active_week.id
        ).first()

        if not user_league:
            # User might not be in a league yet for this week
            return self.join_league(user_id)

        group = user_league.group
        division = group.division

        # Get all members of the group to calculate rank
        group_members = self.db.query(UserLeague).filter(
            UserLeague.league_group_id == group.id
        ).order_by(desc(UserLeague.weekly_xp)).all()

        rank = -1
        for i, member in enumerate(group_members):
            if member.user_id == user_id:
                rank = i + 1
                break

        total_participants = len(group_members)
        promo_spots = division.promotion_spots or 10
        releg_spots = division.relegation_spots or 5
        
        zone = "safe"
        if rank <= promo_spots:
            zone = "promotion"
        elif rank > total_participants - releg_spots:
            zone = "relegation"

        return {
            "division": {
                "id": division.id,
                "name": division.name,
                "tier": division.tier,
                "color": division.color_hex,
            },
            "group_id": group.id,
            "rank": rank,
            "zone": zone,
            "weekly_xp": user_league.weekly_xp,
            "week_ends_at": active_week.week_end,
            "promotion_threshold": promo_spots,
            "relegation_threshold": total_participants - releg_spots + 1,
            "participants": total_participants,
        }

    def get_leaderboard(self, user_id: UUID) -> dict:
        """
        Retrieves the leaderboard for the user's current group.
        """
        active_week = self.db.query(LeagueWeek).filter(LeagueWeek.is_active == True).first()
        if not active_week:
            raise ValueError("NO_ACTIVE_LEAGUE_WEEK")

        user_league = self.db.query(UserLeague).join(LeagueGroup).filter(
            UserLeague.user_id == user_id,
            LeagueGroup.league_week_id == active_week.id
        ).first()
        
        if not user_league:
            raise ValueError("USER_NOT_IN_LEAGUE")

        group = user_league.group
        division = group.division
        
        group_members = self.db.query(UserLeague, User).join(User, UserLeague.user_id == User.id).filter(
            UserLeague.league_group_id == group.id
        ).order_by(desc(UserLeague.weekly_xp)).all()

        leaderboard_list = []
        my_rank = -1
        my_xp = 0
        my_zone = "safe"
        
        total_participants = len(group_members)
        promo_spots = division.promotion_spots or 10
        releg_spots = division.relegation_spots or 5

        for i, (member, user) in enumerate(group_members):
            rank = i + 1
            zone = "safe"
            if rank <= promo_spots:
                zone = "promotion"
            elif rank > total_participants - releg_spots:
                zone = "relegation"
            
            is_me = member.user_id == user_id
            if is_me:
                my_rank = rank
                my_xp = member.weekly_xp
                my_zone = zone

            leaderboard_list.append({
                "user_id": user.id,
                "name": user.display_name or user.username,
                "avatar_url": getattr(user, 'avatar_url', None),
                "xp": member.weekly_xp,
                "rank": rank,
                "zone": zone,
                "is_me": is_me,
            })
            
        return {
            "leaderboard": leaderboard_list,
            "my_rank": my_rank,
            "my_xp": my_xp,
            "my_zone": my_zone,
            "total_participants": total_participants,
        }

    def join_league(self, user_id: UUID) -> dict:
        """
        Joins a user to a league, placing them in an appropriate group.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("USER_NOT_FOUND")

        active_week = self.db.query(LeagueWeek).filter(LeagueWeek.is_active == True).first()
        if not active_week:
            # This should be a server-side issue, maybe create a week?
            # For now, let's raise an error.
            raise ValueError("NO_ACTIVE_LEAGUE_WEEK")

        # Check if user is already in a group for this week
        existing_league = self.db.query(UserLeague).join(LeagueGroup).filter(
            UserLeague.user_id == user_id,
            LeagueGroup.league_week_id == active_week.id
        ).first()
        if existing_league:
            raise ValueError("USER_ALREADY_IN_LEAGUE")

        # Find Bronze division (tier 1)
        bronze_division = self.db.query(LeagueDivision).filter(LeagueDivision.tier == 1).first()
        if not bronze_division:
            raise ValueError("BRONZE_DIVISION_NOT_FOUND")

        # Find a group with space
        target_group = self.db.query(LeagueGroup).join(UserLeague).group_by(LeagueGroup.id).filter(
            LeagueGroup.league_week_id == active_week.id,
            LeagueGroup.division_id == bronze_division.id,
        ).having(func.count(UserLeague.id) < LeagueGroup.max_members).first()

        if not target_group:
            # Create a new group
            last_group_num = self.db.query(func.max(LeagueGroup.group_number)).filter(
                LeagueGroup.league_week_id == active_week.id,
                LeagueGroup.division_id == bronze_division.id
            ).scalar() or 0

            target_group = LeagueGroup(
                league_week_id=active_week.id,
                division_id=bronze_division.id,
                group_number=last_group_num + 1,
                max_members=30
            )
            self.db.add(target_group)
            self.db.flush() # To get the ID

        # Add user to the group
        new_user_league = UserLeague(
            user_id=user_id,
            league_group_id=target_group.id,
            weekly_xp=0,
            current_rank=target_group.members.count() + 1
        )
        self.db.add(new_user_league)
        self.db.commit()

        # Recalculate rank for the new status
        return self.get_current_league_status(user_id)


    def get_league_history(self, user_id: UUID) -> dict:
        """
        Retrieves the league history for a user.
        """
        history_entries = self.db.query(UserLeagueHistory).filter(
            UserLeagueHistory.user_id == user_id
        ).order_by(desc(UserLeagueHistory.created_at)).limit(20).all()

        weeks = []
        for entry in history_entries:
            division = self.db.query(LeagueDivision).filter(LeagueDivision.id == entry.division_id).first()
            week = self.db.query(LeagueWeek).filter(LeagueWeek.id == entry.league_week_id).first()
            weeks.append({
                "week_id": entry.league_week_id,
                "week_start": week.week_start.isoformat() if week else None,
                "week_end": week.week_end.isoformat() if week else None,
                "division_name": division.name if division else "Unknown",
                "final_rank": entry.final_rank,
                "final_xp": entry.final_xp,
                "status": entry.status,
                "gold_earned": entry.gems_earned, # The model calls it gems, API contract says gold
            })
            
        return {"weeks": weeks}
