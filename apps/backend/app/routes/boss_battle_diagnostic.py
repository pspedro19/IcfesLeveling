"""
Boss Battle Diagnostic Integration Routes
Routes for creating and managing boss battles based on diagnostic test performance
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user
from ..services.diagnostic_gamification_service import DiagnosticGamificationService
from ..models.user import User
from ..models.diagnostic_test import DiagnosticTest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/boss-battles/diagnostic", tags=["boss-battles-diagnostic"])

class BossBattleCreate(BaseModel):
    test_id: str

class BossBattleAction(BaseModel):
    action_type: str  # "attack", "defend", "special"
    power_multiplier: float = 1.0

class BossBattleResponse(BaseModel):
    battle_id: str
    boss_name: str
    boss_hp: int
    boss_max_hp: int
    user_hp: int
    user_max_hp: int
    turn_number: int
    battle_status: str  # "ongoing", "victory", "defeat"
    last_action_result: Optional[Dict[str, Any]] = None

@router.post("/create", response_model=Dict[str, Any])
async def create_boss_battle_from_diagnostic(
    battle_data: BossBattleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a boss battle based on diagnostic test performance"""
    try:
        gamification_service = DiagnosticGamificationService(db)
        
        # Verify test ownership and completion
        test = db.query(DiagnosticTest).filter(
            DiagnosticTest.id == battle_data.test_id,
            DiagnosticTest.user_id == current_user.id,
            DiagnosticTest.status == "completed"
        ).first()
        
        if not test:
            raise HTTPException(status_code=404, detail="Test no encontrado o no completado")
        
        # Check if test score qualifies for boss battle
        if test.score_percentage < 70:
            raise HTTPException(
                status_code=400, 
                detail=f"Necesitas al menos 70% para desbloquear batallas jefe. Tu puntuación: {test.score_percentage}%"
            )
        
        # Create boss battle configuration
        boss_config = gamification_service.create_boss_battle_from_diagnostic(str(test.id))
        
        if not boss_config:
            raise HTTPException(status_code=400, detail="No se pudo crear batalla jefe para este test")
        
        # Initialize battle state
        battle_state = {
            "battle_id": boss_config["boss_id"],
            "user_id": str(current_user.id),
            "test_id": str(test.id),
            "boss_config": boss_config,
            "user_hp": current_user.hp,
            "user_max_hp": current_user.hp,
            "boss_hp": boss_config["boss_stats"]["hp"],
            "boss_max_hp": boss_config["boss_stats"]["hp"],
            "turn_number": 1,
            "battle_status": "ongoing",
            "battle_log": [],
            "created_at": datetime.utcnow(),
            "user_power": current_user.power,
            "user_wisdom": current_user.wisdom,
            "user_speed": current_user.speed
        }
        
        # Store battle state (in a real implementation, this would go to a battles table)
        # For now, we'll store it in the test's score_by_topic field
        test.score_by_topic["active_boss_battle"] = battle_state
        db.commit()
        
        logger.info(f"Created boss battle {boss_config['boss_id']} for user {current_user.id}")
        
        return {
            "success": True,
            "battle_id": boss_config["boss_id"],
            "boss_name": boss_config["boss_name"],
            "boss_type": boss_config["boss_type"],
            "boss_level": boss_config["boss_level"],
            "battle_state": {
                "user_hp": battle_state["user_hp"],
                "user_max_hp": battle_state["user_max_hp"],
                "boss_hp": battle_state["boss_hp"],
                "boss_max_hp": battle_state["boss_max_hp"],
                "turn_number": 1,
                "status": "ongoing"
            },
            "rewards_preview": boss_config["rewards"],
            "battle_modifiers": boss_config["battle_modifiers"],
            "message": f"¡Has desbloqueado una batalla épica contra {boss_config['boss_name']}! Tu excelente rendimiento en {test.subject.name if test.subject else 'el diagnóstico'} te ha ganado este desafío especial."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating boss battle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creando batalla jefe: {str(e)}")

@router.post("/battles/{battle_id}/action", response_model=BossBattleResponse)
async def execute_battle_action(
    battle_id: str,
    action: BossBattleAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a battle action in an ongoing boss battle"""
    try:
        # Find the battle state
        battle_test = db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == current_user.id
        ).all()
        
        battle_state = None
        active_test = None
        
        for test in battle_test:
            battle_data = test.score_by_topic.get("active_boss_battle")
            if battle_data and battle_data.get("battle_id") == battle_id:
                battle_state = battle_data
                active_test = test
                break
        
        if not battle_state or not active_test:
            raise HTTPException(status_code=404, detail="Batalla no encontrada")
        
        if battle_state["battle_status"] != "ongoing":
            raise HTTPException(status_code=400, detail="La batalla ya terminó")
        
        # Execute user action
        action_result = _execute_user_action(battle_state, action, current_user)
        battle_state["battle_log"].append(action_result)
        
        # Check if boss is defeated
        if battle_state["boss_hp"] <= 0:
            victory_result = _handle_battle_victory(battle_state, current_user, db)
            battle_state["battle_status"] = "victory"
            battle_state["victory_rewards"] = victory_result
            
            # Apply rewards to user
            _apply_boss_battle_rewards(current_user, victory_result, db)
            
        # Execute boss action if battle continues
        elif battle_state["battle_status"] == "ongoing":
            boss_action_result = _execute_boss_action(battle_state, current_user)
            battle_state["battle_log"].append(boss_action_result)
            
            # Check if user is defeated
            if battle_state["user_hp"] <= 0:
                battle_state["battle_status"] = "defeat"
                defeat_result = _handle_battle_defeat(battle_state)
                battle_state["defeat_consolation"] = defeat_result
        
        battle_state["turn_number"] += 1
        
        # Update battle state
        active_test.score_by_topic["active_boss_battle"] = battle_state
        db.commit()
        
        return BossBattleResponse(
            battle_id=battle_id,
            boss_name=battle_state["boss_config"]["boss_name"],
            boss_hp=max(0, battle_state["boss_hp"]),
            boss_max_hp=battle_state["boss_max_hp"],
            user_hp=max(0, battle_state["user_hp"]),
            user_max_hp=battle_state["user_max_hp"],
            turn_number=battle_state["turn_number"],
            battle_status=battle_state["battle_status"],
            last_action_result=action_result if battle_state["battle_log"] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing battle action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando acción: {str(e)}")

@router.get("/battles/{battle_id}/status")
async def get_battle_status(
    battle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current status of a boss battle"""
    try:
        # Find the battle state
        battle_test = db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == current_user.id
        ).all()
        
        battle_state = None
        
        for test in battle_test:
            battle_data = test.score_by_topic.get("active_boss_battle")
            if battle_data and battle_data.get("battle_id") == battle_id:
                battle_state = battle_data
                break
        
        if not battle_state:
            raise HTTPException(status_code=404, detail="Batalla no encontrada")
        
        return {
            "battle_id": battle_id,
            "boss_name": battle_state["boss_config"]["boss_name"],
            "boss_type": battle_state["boss_config"]["boss_type"],
            "boss_level": battle_state["boss_config"]["boss_level"],
            "battle_status": battle_state["battle_status"],
            "turn_number": battle_state["turn_number"],
            "user_stats": {
                "hp": max(0, battle_state["user_hp"]),
                "max_hp": battle_state["user_max_hp"],
                "power": battle_state["user_power"],
                "wisdom": battle_state["user_wisdom"],
                "speed": battle_state["user_speed"]
            },
            "boss_stats": {
                "hp": max(0, battle_state["boss_hp"]),
                "max_hp": battle_state["boss_max_hp"],
                "power": battle_state["boss_config"]["boss_stats"]["power"]
            },
            "battle_log": battle_state["battle_log"][-5:],  # Last 5 actions
            "rewards_preview": battle_state["boss_config"]["rewards"],
            "victory_rewards": battle_state.get("victory_rewards"),
            "defeat_consolation": battle_state.get("defeat_consolation")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting battle status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@router.get("/available")
async def get_available_boss_battles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available boss battles based on completed diagnostic tests"""
    try:
        gamification_service = DiagnosticGamificationService(db)
        
        # Get user's completed diagnostic tests with high scores
        completed_tests = db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == current_user.id,
            DiagnosticTest.status == "completed",
            DiagnosticTest.score_percentage >= 70
        ).order_by(DiagnosticTest.completed_at.desc()).limit(10).all()
        
        available_battles = []
        
        for test in completed_tests:
            # Check if boss battle already created for this test
            existing_battle = test.score_by_topic.get("active_boss_battle")
            if existing_battle and existing_battle.get("battle_status") == "ongoing":
                # Battle in progress
                available_battles.append({
                    "test_id": str(test.id),
                    "subject": test.subject.name if test.subject else "General",
                    "score": test.score_percentage,
                    "battle_id": existing_battle["battle_id"],
                    "boss_name": existing_battle["boss_config"]["boss_name"],
                    "status": "in_progress",
                    "boss_hp_percentage": (existing_battle["boss_hp"] / existing_battle["boss_max_hp"]) * 100
                })
            elif not existing_battle or existing_battle.get("battle_status") in ["victory", "defeat"]:
                # Can create new battle
                boss_config = gamification_service.create_boss_battle_from_diagnostic(str(test.id))
                if boss_config:
                    available_battles.append({
                        "test_id": str(test.id),
                        "subject": test.subject.name if test.subject else "General",
                        "score": test.score_percentage,
                        "boss_name": boss_config["boss_name"],
                        "boss_type": boss_config["boss_type"],
                        "boss_level": boss_config["boss_level"],
                        "status": "available",
                        "rewards_preview": boss_config["rewards"],
                        "completed_at": test.completed_at,
                        "unlock_message": f"Desbloqueado por obtener {test.score_percentage}% en {test.subject.name if test.subject else 'diagnóstico'}"
                    })
        
        return {
            "available_battles": available_battles,
            "total_available": len([b for b in available_battles if b["status"] == "available"]),
            "battles_in_progress": len([b for b in available_battles if b["status"] == "in_progress"]),
            "user_battle_stats": {
                "power": current_user.power,
                "wisdom": current_user.wisdom,
                "speed": current_user.speed,
                "hp": current_user.hp,
                "level": current_user.level,
                "rank": current_user.rank
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting available boss battles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo batallas disponibles: {str(e)}")

@router.delete("/battles/{battle_id}")
async def forfeit_boss_battle(
    battle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Forfeit an ongoing boss battle"""
    try:
        # Find and end the battle
        battle_test = db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == current_user.id
        ).all()
        
        for test in battle_test:
            battle_data = test.score_by_topic.get("active_boss_battle")
            if battle_data and battle_data.get("battle_id") == battle_id:
                if battle_data["battle_status"] == "ongoing":
                    battle_data["battle_status"] = "forfeited"
                    battle_data["forfeited_at"] = datetime.utcnow()
                    
                    # Give small consolation reward
                    consolation_xp = 25
                    current_user.add_experience(consolation_xp)
                    
                    test.score_by_topic["active_boss_battle"] = battle_data
                    db.commit()
                    
                    return {
                        "success": True,
                        "message": "Batalla abandonada",
                        "consolation_reward": {
                            "xp": consolation_xp,
                            "message": "No te rindas, cada intento te hace más fuerte"
                        }
                    }
                else:
                    raise HTTPException(status_code=400, detail="La batalla ya terminó")
        
        raise HTTPException(status_code=404, detail="Batalla no encontrada")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forfeiting boss battle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error abandonando batalla: {str(e)}")

# Helper functions for battle mechanics

def _execute_user_action(battle_state: Dict, action: BossBattleAction, user: User) -> Dict[str, Any]:
    """Execute user's battle action"""
    import random
    
    base_damage = user.power
    action_result = {
        "actor": "user",
        "action": action.action_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if action.action_type == "attack":
        # Calculate damage with some randomness
        damage = int(base_damage * action.power_multiplier * random.uniform(0.8, 1.2))
        critical = random.random() < (user.speed / 200)  # Speed affects crit chance
        
        if critical:
            damage = int(damage * 1.5)
            action_result["critical"] = True
            action_result["message"] = f"¡GOLPE CRÍTICO! Infliges {damage} de daño"
        else:
            action_result["message"] = f"Atacas e infliges {damage} de daño"
        
        battle_state["boss_hp"] -= damage
        action_result["damage"] = damage
        
    elif action.action_type == "defend":
        # Defending restores some HP and reduces next boss damage
        heal = int(user.wisdom * 0.5)
        battle_state["user_hp"] = min(battle_state["user_max_hp"], battle_state["user_hp"] + heal)
        battle_state["defense_active"] = True
        
        action_result["heal"] = heal
        action_result["message"] = f"Te defiendes y recuperas {heal} HP. Preparado para el próximo ataque."
        
    elif action.action_type == "special":
        # Special attack based on user's wisdom
        special_damage = int((user.power + user.wisdom) * 0.8 * action.power_multiplier)
        mp_cost = 10
        
        if user.mp >= mp_cost:
            battle_state["boss_hp"] -= special_damage
            action_result["damage"] = special_damage
            action_result["mp_cost"] = mp_cost
            action_result["message"] = f"¡ATAQUE ESPECIAL! Infliges {special_damage} de daño mágico"
        else:
            action_result["message"] = "No tienes suficiente MP para el ataque especial"
            action_result["failed"] = True
    
    return action_result

def _execute_boss_action(battle_state: Dict, user: User) -> Dict[str, Any]:
    """Execute boss's action"""
    import random
    
    boss_config = battle_state["boss_config"]
    boss_power = boss_config["boss_stats"]["power"]
    
    # Boss chooses action based on HP percentage
    boss_hp_percentage = battle_state["boss_hp"] / battle_state["boss_max_hp"]
    
    if boss_hp_percentage < 0.3:
        # Boss is desperate, uses powerful attacks
        action_type = "desperate_attack"
        damage = int(boss_power * random.uniform(1.2, 1.5))
        message = f"{boss_config['boss_name']} entra en modo berserk e inflige {damage} de daño"
    elif boss_hp_percentage < 0.6:
        # Boss uses special abilities
        action_type = "special_ability"
        damage = int(boss_power * random.uniform(0.9, 1.3))
        message = f"{boss_config['boss_name']} usa una habilidad especial e inflige {damage} de daño"
    else:
        # Normal attack
        action_type = "normal_attack"
        damage = int(boss_power * random.uniform(0.7, 1.1))
        message = f"{boss_config['boss_name']} ataca e inflige {damage} de daño"
    
    # Apply defense reduction if user defended
    if battle_state.get("defense_active"):
        damage = int(damage * 0.6)
        message += " (daño reducido por defensa)"
        battle_state["defense_active"] = False
    
    battle_state["user_hp"] -= damage
    
    return {
        "actor": "boss",
        "action": action_type,
        "damage": damage,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

def _handle_battle_victory(battle_state: Dict, user: User, db: Session) -> Dict[str, Any]:
    """Handle boss battle victory"""
    boss_config = battle_state["boss_config"]
    rewards = boss_config["rewards"]
    
    # Calculate bonus based on performance
    remaining_hp_bonus = (battle_state["user_hp"] / battle_state["user_max_hp"]) * 0.2
    turn_efficiency_bonus = max(0, (20 - battle_state["turn_number"]) / 20 * 0.3)
    
    total_multiplier = 1.0 + remaining_hp_bonus + turn_efficiency_bonus
    
    victory_rewards = {
        "xp": int(rewards["xp"] * total_multiplier),
        "crystals": int(rewards["crystals"] * total_multiplier),
        "orbs": int(rewards["orbs"] * total_multiplier),
        "special_item": rewards.get("special_item"),
        "performance_bonus": {
            "hp_bonus": remaining_hp_bonus,
            "efficiency_bonus": turn_efficiency_bonus,
            "total_multiplier": total_multiplier
        },
        "victory_title": _get_victory_title(battle_state, boss_config),
        "achievement": f"Derrotaste a {boss_config['boss_name']}"
    }
    
    return victory_rewards

def _handle_battle_defeat(battle_state: Dict) -> Dict[str, Any]:
    """Handle boss battle defeat"""
    return {
        "consolation_xp": 50,
        "consolation_orbs": 25,
        "message": "La derrota es solo el comienzo de la sabiduría",
        "retry_available": True,
        "tip": "Mejora tus stats con más diagnósticos antes de reintentar"
    }

def _apply_boss_battle_rewards(user: User, rewards: Dict[str, Any], db: Session):
    """Apply boss battle rewards to user"""
    user.add_experience(rewards["xp"])
    user.crystals += rewards["crystals"]
    user.orbs += rewards["orbs"]
    
    # Small stat boosts for victory
    user.power = min(100, user.power + 1)
    user.wisdom = min(100, user.wisdom + 1)
    
    db.commit()

def _get_victory_title(battle_state: Dict, boss_config: Dict) -> str:
    """Get victory title based on performance"""
    turns = battle_state["turn_number"]
    hp_remaining = battle_state["user_hp"] / battle_state["user_max_hp"]
    
    if turns <= 5 and hp_remaining > 0.8:
        return "Dominación Absoluta"
    elif turns <= 8 and hp_remaining > 0.6:
        return "Victoria Épica"
    elif turns <= 12 and hp_remaining > 0.4:
        return "Victoria Sólida"
    elif hp_remaining > 0.2:
        return "Victoria por los Pelos"
    else:
        return "Victoria Pírrica"