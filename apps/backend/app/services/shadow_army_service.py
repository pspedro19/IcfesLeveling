from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
import json

from ..models.shadow_army import (
    ShadowSoldier, ShadowFormation, ShadowBattle, ShadowExtraction, 
    ShadowAbility, UserShadowStats
)
from ..models.user import User
from ..models.battle import Battle
from ..services.achievement_service import AchievementService

class ShadowArmyService:
    def __init__(self, db: Session):
        self.db = db
        self.achievement_service = AchievementService(db)
    
    def initialize_user_shadow_system(self, user_id: str) -> UserShadowStats:
        """Initialize shadow system for a user"""
        existing_stats = self.db.query(UserShadowStats).filter(
            UserShadowStats.user_id == user_id
        ).first()
        
        if existing_stats:
            return existing_stats
        
        shadow_stats = UserShadowStats(
            user_id=user_id,
            monarch_level=1,
            shadow_capacity=5,
            extraction_power=100
        )
        
        self.db.add(shadow_stats)
        self.db.commit()
        self.db.refresh(shadow_stats)
        
        return shadow_stats
    
    def get_user_shadow_stats(self, user_id: str) -> Optional[UserShadowStats]:
        """Get user's shadow monarch stats"""
        return self.db.query(UserShadowStats).filter(
            UserShadowStats.user_id == user_id
        ).first()
    
    def get_user_shadows(self, user_id: str, active_only: bool = True) -> List[ShadowSoldier]:
        """Get user's shadow army"""
        query = self.db.query(ShadowSoldier).filter(ShadowSoldier.user_id == user_id)
        if active_only:
            query = query.filter(ShadowSoldier.is_active == True)
        return query.order_by(desc(ShadowSoldier.level), desc(ShadowSoldier.attack_power)).all()
    
    def attempt_shadow_extraction(self, user_id: str, enemy_name: str, enemy_level: int, 
                                battle_id: str = None) -> Dict[str, Any]:
        """Attempt to extract shadow from defeated enemy"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "User not found"}
        
        shadow_stats = self.get_user_shadow_stats(user_id)
        if not shadow_stats:
            shadow_stats = self.initialize_user_shadow_system(user_id)
        
        # Check if user can extract
        if not shadow_stats.can_extract_shadow():
            return {
                "success": False, 
                "message": "Cannot extract: Shadow capacity full or insufficient extraction power"
            }
        
        # Calculate extraction chance
        extraction_chance = shadow_stats.get_extraction_chance(enemy_level, user.level)
        success = random.random() * 100 <= extraction_chance
        
        # Record extraction attempt
        extraction = ShadowExtraction(
            user_id=user_id,
            source_enemy=enemy_name,
            source_battle_id=battle_id,
            extraction_success=success,
            enemy_level=enemy_level,
            user_level_at_extraction=user.level,
            extraction_chance=extraction_chance
        )
        
        self.db.add(extraction)
        
        if success:
            # Create shadow soldier
            shadow_type = self._determine_shadow_type(enemy_name, enemy_level)
            shadow = self._create_shadow_soldier(user_id, enemy_name, shadow_type, enemy_level, extraction)
            
            # Update user stats
            shadow_stats.total_shadows_extracted += 1
            shadow_stats.active_shadows += 1
            shadow_stats.extraction_power -= 20  # Cost of extraction
            
            # Check achievements
            self.achievement_service.update_achievement_progress(
                user_id, 
                "shadow_arise_achievement_id",  # Would need actual achievement ID
                1,
                {"shadow_type": shadow_type, "shadow_name": shadow.name}
            )
            
            self.db.commit()
            self.db.refresh(shadow)
            
            return {
                "success": True,
                "message": f"Successfully extracted shadow: {shadow.name}",
                "shadow": {
                    "id": str(shadow.id),
                    "name": shadow.name,
                    "type": shadow.shadow_type,
                    "rank": shadow.rank,
                    "stats": {
                        "attack": shadow.attack_power,
                        "defense": shadow.defense,
                        "magic": shadow.magic_power,
                        "speed": shadow.speed
                    }
                },
                "extraction_chance": extraction_chance
            }
        else:
            # Failed extraction
            shadow_stats.extraction_power -= 10  # Partial cost for failed attempt
            self.db.commit()
            
            return {
                "success": False,
                "message": f"Shadow extraction failed (chance: {extraction_chance:.1f}%)",
                "extraction_chance": extraction_chance,
                "retry_possible": shadow_stats.extraction_power >= 10
            }
    
    def _determine_shadow_type(self, enemy_name: str, enemy_level: int) -> str:
        """Determine shadow type based on enemy characteristics"""
        enemy_lower = enemy_name.lower()
        
        # Rule-based shadow type assignment
        if any(word in enemy_lower for word in ['knight', 'guard', 'warrior', 'soldier']):
            return 'knight'
        elif any(word in enemy_lower for word in ['mage', 'wizard', 'witch', 'sorcerer']):
            return 'mage'
        elif any(word in enemy_lower for word in ['archer', 'ranger', 'hunter', 'sniper']):
            return 'archer'
        elif any(word in enemy_lower for word in ['assassin', 'rogue', 'ninja', 'thief']):
            return 'assassin'
        elif any(word in enemy_lower for word in ['beast', 'wolf', 'dragon', 'monster']):
            return 'beast'
        else:
            # Random assignment for generic enemies
            return random.choice(['knight', 'mage', 'archer', 'assassin', 'beast'])
    
    def _create_shadow_soldier(self, user_id: str, enemy_name: str, shadow_type: str, 
                             enemy_level: int, extraction: ShadowExtraction) -> ShadowSoldier:
        """Create a new shadow soldier"""
        # Base stats influenced by enemy level and type
        base_stats = {
            'knight': {'attack': 15, 'defense': 20, 'magic': 5, 'speed': 8, 'health': 150, 'mana': 30},
            'mage': {'attack': 8, 'defense': 10, 'magic': 25, 'speed': 12, 'health': 100, 'mana': 100},
            'archer': {'attack': 18, 'defense': 12, 'magic': 10, 'speed': 20, 'health': 120, 'mana': 50},
            'assassin': {'attack': 20, 'defense': 8, 'magic': 12, 'speed': 25, 'health': 110, 'mana': 60},
            'beast': {'attack': 22, 'defense': 15, 'magic': 5, 'speed': 15, 'health': 140, 'mana': 40}
        }
        
        stats = base_stats[shadow_type]
        level_multiplier = max(1, enemy_level // 10)
        
        shadow = ShadowSoldier(
            user_id=user_id,
            name=f"Shadow {enemy_name}",
            shadow_type=shadow_type,
            rank='E',  # All shadows start at E rank
            level=max(1, enemy_level - 5),  # Slightly lower than enemy
            experience=0,
            attack_power=stats['attack'] * level_multiplier,
            defense=stats['defense'] * level_multiplier,
            magic_power=stats['magic'] * level_multiplier,
            speed=stats['speed'] * level_multiplier,
            health=stats['health'] * level_multiplier,
            mana=stats['mana'] * level_multiplier,
            extraction_source=enemy_name,
            special_abilities=self._get_initial_abilities(shadow_type)
        )
        
        self.db.add(shadow)
        extraction.shadow_soldier_id = shadow.id  # Link extraction to shadow
        
        return shadow
    
    def _get_initial_abilities(self, shadow_type: str) -> List[str]:
        """Get initial abilities for shadow type"""
        initial_abilities = {
            'knight': ['Shield Bash', 'Taunt'],
            'mage': ['Magic Missile', 'Mana Shield'],
            'archer': ['Precise Shot', 'Eagle Eye'],
            'assassin': ['Stealth Strike', 'Poison Blade'],
            'beast': ['Savage Bite', 'Pack Mentality']
        }
        return initial_abilities.get(shadow_type, ['Basic Attack'])
    
    def summon_shadow(self, user_id: str, shadow_id: str) -> Dict[str, Any]:
        """Summon a shadow for battle"""
        shadow = self.db.query(ShadowSoldier).filter(
            and_(ShadowSoldier.id == shadow_id, ShadowSoldier.user_id == user_id)
        ).first()
        
        if not shadow:
            return {"success": False, "message": "Shadow not found"}
        
        if not shadow.is_active:
            return {"success": False, "message": "Shadow is not active"}
        
        shadow.is_summoned = True
        shadow.last_battle = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Shadow {shadow.name} summoned for battle",
            "shadow": {
                "id": str(shadow.id),
                "name": shadow.name,
                "type": shadow.shadow_type,
                "level": shadow.level,
                "combat_power": shadow.get_combat_power()
            }
        }
    
    def dismiss_shadow(self, user_id: str, shadow_id: str) -> Dict[str, Any]:
        """Dismiss a summoned shadow"""
        shadow = self.db.query(ShadowSoldier).filter(
            and_(ShadowSoldier.id == shadow_id, ShadowSoldier.user_id == user_id)
        ).first()
        
        if not shadow:
            return {"success": False, "message": "Shadow not found"}
        
        shadow.is_summoned = False
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Shadow {shadow.name} dismissed"
        }
    
    def evolve_shadow(self, user_id: str, shadow_id: str) -> Dict[str, Any]:
        """Evolve a shadow to next rank"""
        shadow = self.db.query(ShadowSoldier).filter(
            and_(ShadowSoldier.id == shadow_id, ShadowSoldier.user_id == user_id)
        ).first()
        
        if not shadow:
            return {"success": False, "message": "Shadow not found"}
        
        if not shadow.can_evolve():
            return {"success": False, "message": "Shadow doesn't meet evolution requirements"}
        
        old_rank = shadow.rank
        old_power = shadow.get_combat_power()
        
        if shadow.evolve():
            new_power = shadow.get_combat_power()
            
            # Update user shadow stats
            shadow_stats = self.get_user_shadow_stats(user_id)
            if shadow_stats:
                rank_order = ['E', 'D', 'C', 'B', 'A', 'S', 'SS']
                if rank_order.index(shadow.rank) > rank_order.index(shadow_stats.highest_rank_shadow):
                    shadow_stats.highest_rank_shadow = shadow.rank
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Shadow {shadow.name} evolved from {old_rank} to {shadow.rank}!",
                "shadow": {
                    "id": str(shadow.id),
                    "name": shadow.name,
                    "old_rank": old_rank,
                    "new_rank": shadow.rank,
                    "power_increase": new_power - old_power,
                    "new_stats": {
                        "attack": shadow.attack_power,
                        "defense": shadow.defense,
                        "magic": shadow.magic_power,
                        "speed": shadow.speed,
                        "health": shadow.health,
                        "mana": shadow.mana
                    }
                }
            }
        else:
            return {"success": False, "message": "Evolution failed"}
    
    def create_formation(self, user_id: str, name: str, formation_type: str, 
                        shadow_positions: Dict[str, str]) -> Dict[str, Any]:
        """Create a shadow formation"""
        # Validate shadows belong to user
        user_shadows = {str(s.id): s for s in self.get_user_shadows(user_id)}
        
        for position, shadow_id in shadow_positions.items():
            if shadow_id not in user_shadows:
                return {"success": False, "message": f"Shadow {shadow_id} not found"}
        
        formation = ShadowFormation(
            user_id=user_id,
            name=name,
            formation_type=formation_type,
            shadow_positions=shadow_positions,
            formation_bonuses=self._calculate_formation_bonuses(formation_type, shadow_positions, user_shadows)
        )
        
        self.db.add(formation)
        self.db.commit()
        self.db.refresh(formation)
        
        return {
            "success": True,
            "message": f"Formation '{name}' created successfully",
            "formation": {
                "id": str(formation.id),
                "name": formation.name,
                "type": formation.formation_type,
                "bonuses": formation.formation_bonuses
            }
        }
    
    def _calculate_formation_bonuses(self, formation_type: str, positions: Dict[str, str], 
                                   shadows: Dict[str, ShadowSoldier]) -> Dict[str, Any]:
        """Calculate bonuses based on formation type and shadows"""
        bonuses = {}
        
        if formation_type == 'attack':
            bonuses['attack_bonus'] = 15
            bonuses['critical_chance'] = 10
        elif formation_type == 'defense':
            bonuses['defense_bonus'] = 20
            bonuses['damage_reduction'] = 10
        elif formation_type == 'speed':
            bonuses['speed_bonus'] = 25
            bonuses['first_strike'] = True
        elif formation_type == 'balanced':
            bonuses['all_stats_bonus'] = 10
        
        # Additional bonuses for shadow type synergies
        shadow_types = [shadows[shadow_id].shadow_type for shadow_id in positions.values()]
        unique_types = set(shadow_types)
        
        if len(unique_types) == 1:
            # Mono-type bonus
            bonuses['mono_type_bonus'] = 15
        elif len(unique_types) >= 4:
            # Diverse army bonus
            bonuses['diversity_bonus'] = 20
        
        return bonuses
    
    def get_shadow_battle_history(self, user_id: str, shadow_id: str = None) -> List[Dict[str, Any]]:
        """Get shadow battle history"""
        query = self.db.query(ShadowBattle).filter(ShadowBattle.user_id == user_id)
        
        if shadow_id:
            query = query.filter(ShadowBattle.shadow_soldier_id == shadow_id)
        
        battles = query.order_by(desc(ShadowBattle.created_at)).limit(20).all()
        
        return [
            {
                "id": str(battle.id),
                "shadow_name": battle.shadow_soldier.name if battle.shadow_soldier else "Unknown",
                "damage_dealt": battle.damage_dealt,
                "damage_taken": battle.damage_taken,
                "experience_gained": battle.experience_gained,
                "survived": battle.survived_battle,
                "date": battle.created_at
            }
            for battle in battles
        ]
    
    def get_extraction_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get shadow extraction history"""
        extractions = self.db.query(ShadowExtraction).filter(
            ShadowExtraction.user_id == user_id
        ).order_by(desc(ShadowExtraction.created_at)).limit(limit).all()
        
        return [
            {
                "id": str(extraction.id),
                "source_enemy": extraction.source_enemy,
                "success": extraction.extraction_success,
                "extraction_chance": float(extraction.extraction_chance),
                "enemy_level": extraction.enemy_level,
                "shadow_name": extraction.shadow_soldier.name if extraction.shadow_soldier else None,
                "date": extraction.created_at
            }
            for extraction in extractions
        ]
    
    def regenerate_extraction_power(self, user_id: str) -> Dict[str, Any]:
        """Regenerate user's extraction power over time"""
        shadow_stats = self.get_user_shadow_stats(user_id)
        if not shadow_stats:
            return {"success": False, "message": "Shadow stats not found"}
        
        # Regenerate 1 power per hour, max 100
        hours_since_update = (datetime.utcnow() - shadow_stats.updated_at).total_seconds() / 3600
        power_to_add = min(int(hours_since_update), 100 - shadow_stats.extraction_power)
        
        if power_to_add > 0:
            shadow_stats.extraction_power = min(100, shadow_stats.extraction_power + power_to_add)
            shadow_stats.updated_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "success": True,
                "power_regenerated": power_to_add,
                "current_power": shadow_stats.extraction_power
            }
        
        return {
            "success": False,
            "message": "No power regeneration needed",
            "current_power": shadow_stats.extraction_power
        }