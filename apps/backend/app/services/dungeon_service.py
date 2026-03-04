from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
import json

from ..models.dungeon import DungeonGate, DungeonRun, DungeonEncounter, DungeonMonster, RaidParticipant
from ..models.user import User
from ..models.question import Question
from ..services.shadow_army_service import ShadowArmyService
from ..services.achievement_service import AchievementService

class DungeonService:
    def __init__(self, db: Session):
        self.db = db
        self.shadow_service = ShadowArmyService(db)
        self.achievement_service = AchievementService(db)
    
    def get_available_gates(self, user_id: str, gate_type: str = None, difficulty: str = None) -> List[Dict[str, Any]]:
        """Get available dungeon gates for user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        query = self.db.query(DungeonGate).filter(DungeonGate.is_active == True)
        
        if gate_type:
            query = query.filter(DungeonGate.gate_type == gate_type)
        
        if difficulty:
            query = query.filter(DungeonGate.difficulty_rank == difficulty)
        
        # Check for seasonal gates
        now = datetime.utcnow()
        query = query.filter(
            or_(
                DungeonGate.is_seasonal == False,
                and_(
                    DungeonGate.is_seasonal == True,
                    DungeonGate.seasonal_start <= now,
                    DungeonGate.seasonal_end >= now
                )
            )
        )
        
        gates = query.order_by(DungeonGate.recommended_level, DungeonGate.difficulty_rank).all()
        
        # Filter gates based on user level and rank
        available_gates = []
        for gate in gates:
            if self._can_user_enter_gate(user, gate):
                gate_data = {
                    "id": str(gate.id),
                    "name": gate.name,
                    "description": gate.description,
                    "type": gate.gate_type,
                    "difficulty_rank": gate.difficulty_rank,
                    "recommended_level": gate.recommended_level,
                    "time_limit": gate.time_limit_minutes,
                    "entry_costs": {
                        "orbs": gate.entry_cost_orbs,
                        "crystals": gate.entry_cost_crystals
                    },
                    "rewards": {
                        "experience": gate.base_experience_reward,
                        "orbs": gate.base_orb_reward,
                        "crystals": gate.base_crystal_reward
                    },
                    "stats": {
                        "times_entered": gate.times_entered,
                        "times_completed": gate.times_completed,
                        "success_rate": float(gate.success_rate),
                        "avg_completion_time": gate.average_completion_time
                    },
                    "is_raid": gate.is_raid_gate,
                    "max_participants": gate.max_participants,
                    "is_seasonal": gate.is_seasonal
                }
                available_gates.append(gate_data)
        
        return available_gates
    
    def _can_user_enter_gate(self, user: User, gate: DungeonGate) -> bool:
        """Check if user meets requirements to enter gate"""
        # Level requirement
        if user.level < gate.recommended_level:
            return False
        
        # Rank requirement
        rank_order = ['E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS']
        if rank_order.index(user.rank) < rank_order.index(gate.min_rank_requirement):
            return False
        
        # Currency requirements
        if user.orbs < gate.entry_cost_orbs:
            return False
        if user.crystals < gate.entry_cost_crystals:
            return False
        
        return True
    
    def enter_gate(self, user_id: str, gate_id: str) -> Dict[str, Any]:
        """Start a new dungeon run"""
        user = self.db.query(User).filter(User.id == user_id).first()
        gate = self.db.query(DungeonGate).filter(DungeonGate.id == gate_id).first()
        
        if not user or not gate:
            return {"success": False, "message": "User or gate not found"}
        
        if not self._can_user_enter_gate(user, gate):
            return {"success": False, "message": "Requirements not met to enter this gate"}
        
        # Check for existing active runs
        active_run = self.db.query(DungeonRun).filter(
            and_(
                DungeonRun.user_id == user_id,
                DungeonRun.status == "in_progress"
            )
        ).first()
        
        if active_run:
            return {"success": False, "message": "You already have an active dungeon run"}
        
        # Deduct entry costs
        user.orbs -= gate.entry_cost_orbs
        user.crystals -= gate.entry_cost_crystals
        
        # Create dungeon run
        dungeon_run = DungeonRun(
            gate_id=gate_id,
            user_id=user_id,
            status="in_progress",
            current_room=1
        )
        
        self.db.add(dungeon_run)
        
        # Update gate statistics
        gate.times_entered += 1
        
        self.db.commit()
        self.db.refresh(dungeon_run)
        
        # Generate first room encounter
        first_encounter = self._generate_room_encounter(dungeon_run, 1)
        
        return {
            "success": True,
            "message": f"Entered {gate.name}",
            "run_id": str(dungeon_run.id),
            "gate_info": {
                "name": gate.name,
                "total_rooms": gate.total_rooms,
                "time_limit": gate.time_limit_minutes
            },
            "current_encounter": first_encounter
        }
    
    def _generate_room_encounter(self, dungeon_run: DungeonRun, room_number: int) -> Dict[str, Any]:
        """Generate encounter for specific room"""
        gate = dungeon_run.gate
        room_config = gate.room_configuration or {}
        
        # Get room configuration or generate default
        if isinstance(room_config, list) and len(room_config) >= room_number:
            room_data = room_config[room_number - 1]
        else:
            # Generate default encounter
            if room_number == gate.boss_room:
                room_data = {"type": "boss", "enemies": []}
            else:
                room_data = {"type": "monster", "enemies": []}
        
        encounter_type = room_data.get("type", "monster")
        
        # Select appropriate monster(s) for this room
        if encounter_type == "boss":
            monsters = self.db.query(DungeonMonster).filter(
                and_(
                    DungeonMonster.is_boss == True,
                    DungeonMonster.rank == gate.difficulty_rank,
                    DungeonMonster.is_active == True
                )
            ).all()
        else:
            monsters = self.db.query(DungeonMonster).filter(
                and_(
                    DungeonMonster.is_boss == False,
                    DungeonMonster.rank == gate.difficulty_rank,
                    DungeonMonster.is_active == True
                )
            ).all()
        
        if not monsters:
            # Fallback to any monster of appropriate rank
            monsters = self.db.query(DungeonMonster).filter(
                and_(
                    DungeonMonster.rank == gate.difficulty_rank,
                    DungeonMonster.is_active == True
                )
            ).all()
        
        if not monsters:
            return {"success": False, "message": "No monsters available for this encounter"}
        
        # Select random monster
        selected_monster = random.choice(monsters)
        
        # Create encounter record
        encounter = DungeonEncounter(
            dungeon_run_id=dungeon_run.id,
            room_number=room_number,
            encounter_type=encounter_type,
            enemy_name=selected_monster.name,
            enemy_level=selected_monster.level,
            enemy_type=selected_monster.monster_type
        )
        
        self.db.add(encounter)
        self.db.commit()
        self.db.refresh(encounter)
        
        return {
            "encounter_id": str(encounter.id),
            "room_number": room_number,
            "encounter_type": encounter_type,
            "enemy": {
                "name": selected_monster.name,
                "level": selected_monster.level,
                "type": selected_monster.monster_type,
                "health": selected_monster.health,
                "description": selected_monster.description
            },
            "questions_required": selected_monster.questions_per_encounter
        }
    
    def get_questions_for_encounter(self, encounter_id: str) -> List[Dict[str, Any]]:
        """Get questions for dungeon encounter"""
        encounter = self.db.query(DungeonEncounter).filter(
            DungeonEncounter.id == encounter_id
        ).first()
        
        if not encounter:
            return []
        
        monster = self.db.query(DungeonMonster).filter(
            DungeonMonster.name == encounter.enemy_name
        ).first()
        
        if not monster:
            return []
        
        # Get questions based on monster preferences
        query = self.db.query(Question).filter(Question.is_active == True)
        
        if monster.preferred_subjects:
            query = query.filter(Question.subject_id.in_(monster.preferred_subjects))
        
        # Filter by difficulty if specified
        if monster.question_difficulty == "easy":
            query = query.filter(Question.difficulty_level <= 2)
        elif monster.question_difficulty == "hard":
            query = query.filter(Question.difficulty_level >= 4)
        else:  # medium
            query = query.filter(Question.difficulty_level.between(2, 4))
        
        available_questions = query.limit(50).all()  # Get pool of questions
        
        if len(available_questions) < monster.questions_per_encounter:
            # If not enough questions, get any available questions
            available_questions = self.db.query(Question).filter(
                Question.is_active == True
            ).limit(50).all()
        
        # Select random questions
        selected_questions = random.sample(
            available_questions, 
            min(monster.questions_per_encounter, len(available_questions))
        )
        
        # Update encounter with question IDs
        question_ids = [str(q.id) for q in selected_questions]
        encounter.questions_faced = question_ids
        self.db.commit()
        
        return [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
                "image_url": q.image_url,
                "difficulty": q.difficulty_level
            }
            for q in selected_questions
        ]
    
    def submit_encounter_answers(self, encounter_id: str, user_id: str, answers: List[str], 
                               shadows_used: List[str] = None) -> Dict[str, Any]:
        """Submit answers for dungeon encounter"""
        encounter = self.db.query(DungeonEncounter).filter(
            DungeonEncounter.id == encounter_id
        ).first()
        
        if not encounter:
            return {"success": False, "message": "Encounter not found"}
        
        if encounter.dungeon_run.user_id != user_id:
            return {"success": False, "message": "Not your encounter"}
        
        # Get questions and correct answers
        question_ids = encounter.questions_faced or []
        questions = self.db.query(Question).filter(
            Question.id.in_(question_ids)
        ).all()
        
        # Calculate results
        correct_count = 0
        total_questions = len(questions)

        question_dict = {str(q.id): q for q in questions}

        # Build detailed question results with explanations
        question_results = []

        for i, answer in enumerate(answers):
            if i < len(question_ids):
                question = question_dict.get(question_ids[i])
                if question:
                    # Get correct answer - try both field names for compatibility
                    correct_ans = getattr(question, 'correct_answer', None) or getattr(question, 'respuesta_correcta', '')
                    correct_ans = correct_ans.lower() if correct_ans else ''
                    is_correct = correct_ans == answer.lower()

                    if is_correct:
                        correct_count += 1

                    # Get explanation (may be None if not set)
                    explanation = getattr(question, 'explanation', None)

                    # Try to get video URL from video recommendations if question was answered incorrectly
                    video_url = None
                    if not is_correct:
                        try:
                            from ..models.question_video_recommendations import QuestionVideoRecommendations
                            from ..models.youtube_catalog import YoutubeCatalog

                            # Get top video recommendation for this question
                            video_rec = self.db.query(QuestionVideoRecommendations).filter(
                                QuestionVideoRecommendations.question_id == question.id,
                                QuestionVideoRecommendations.is_active == True
                            ).order_by(QuestionVideoRecommendations.total_score.desc()).first()

                            if video_rec and video_rec.video:
                                video_url = video_rec.video.url
                        except Exception:
                            # If video recommendation lookup fails, continue without it
                            pass

                    question_results.append({
                        "question_id": str(question.id),
                        "user_answer": answer,
                        "correct_answer": correct_ans,
                        "is_correct": is_correct,
                        "explanation": explanation,
                        "video_url": video_url
                    })

        accuracy = correct_count / total_questions if total_questions > 0 else 0
        
        # Calculate combat results
        monster = self.db.query(DungeonMonster).filter(
            DungeonMonster.name == encounter.enemy_name
        ).first()
        
        if not monster:
            return {"success": False, "message": "Monster data not found"}
        
        # Combat calculation based on accuracy and shadows
        base_damage = 50
        user_damage = int(base_damage * (0.5 + accuracy))  # 50-100% damage based on accuracy
        
        # Shadow bonuses
        shadow_bonus = 0
        if shadows_used:
            shadow_bonus = len(shadows_used) * 15  # 15 damage per shadow
        
        total_damage = user_damage + shadow_bonus
        
        # Monster damage to user (reduced by accuracy)
        monster_damage = max(5, int(monster.attack * (1.0 - accuracy * 0.8)))
        
        # Determine if encounter won
        encounter_won = accuracy >= 0.6  # Need 60% accuracy to win
        
        # Update encounter
        encounter.answers_given = answers
        encounter.encounter_won = encounter_won
        encounter.damage_dealt = total_damage
        encounter.damage_taken = monster_damage if not encounter_won else 0
        encounter.experience_gained = int(monster.level * 10 * accuracy)
        encounter.orbs_gained = int(monster.orb_drop_min + (monster.orb_drop_max - monster.orb_drop_min) * accuracy)
        encounter.shadows_used = shadows_used or []
        
        # Handle shadow extraction attempt
        extraction_result = None
        if encounter_won and monster.can_be_extracted:
            extraction_result = self.shadow_service.attempt_shadow_extraction(
                user_id, monster.name, monster.level, encounter.dungeon_run.id
            )
            encounter.shadow_extraction_attempted = True
            encounter.shadow_extraction_successful = extraction_result.get("success", False)
        
        # Update dungeon run stats
        dungeon_run = encounter.dungeon_run
        dungeon_run.questions_answered += total_questions
        dungeon_run.questions_correct += correct_count
        dungeon_run.total_damage_dealt += total_damage
        dungeon_run.total_damage_taken += encounter.damage_taken
        dungeon_run.experience_gained += encounter.experience_gained
        dungeon_run.orbs_gained += encounter.orbs_gained
        
        if encounter_won:
            dungeon_run.monsters_defeated += 1
            
            if encounter.encounter_type == "boss":
                dungeon_run.boss_defeated = True
        
        # Check if this was the last room
        gate = dungeon_run.gate
        room_completed = encounter.room_number
        
        if encounter_won and room_completed >= gate.total_rooms:
            # Dungeon completed!
            return self._complete_dungeon_run(dungeon_run, user_id)
        elif encounter_won:
            # Move to next room
            dungeon_run.current_room += 1
            next_encounter = self._generate_room_encounter(dungeon_run, dungeon_run.current_room)
        else:
            # Failed encounter - end run
            dungeon_run.status = "failed"
            dungeon_run.completion_time = datetime.utcnow()
            dungeon_run.total_time_seconds = int((dungeon_run.completion_time - dungeon_run.start_time).total_seconds())
        
        self.db.commit()
        
        # Get current HP values for the response
        user = self.db.query(User).filter(User.id == user_id).first()
        player_max_hp = getattr(user, 'max_hp', 100) if user else 100
        player_current_hp = max(0, player_max_hp - dungeon_run.total_damage_taken)
        enemy_max_hp = monster.health if monster else 100
        enemy_current_hp = max(0, enemy_max_hp - total_damage) if not encounter_won else 0

        result = {
            "success": encounter_won,
            "encounter_results": {
                "accuracy": accuracy,
                "correct_answers": correct_count,
                "total_questions": total_questions,
                "damage_dealt": total_damage,
                "damage_taken": encounter.damage_taken,
                "enemy_current_hp": enemy_current_hp,
                "player_current_hp": player_current_hp,
                "current_combo": dungeon_run.monsters_defeated,  # Combo based on consecutive monsters defeated
                "xp_earned": encounter.experience_gained,
                "experience_gained": encounter.experience_gained,
                "orbs_gained": encounter.orbs_gained,
                "enemy_defeated": encounter_won,
                "player_defeated": dungeon_run.status == "failed"
            },
            "question_results": question_results,  # Detailed results with explanations and video URLs
            "dungeon_status": dungeon_run.status,
            "current_room": dungeon_run.current_room
        }

        if extraction_result:
            result["shadow_extraction"] = extraction_result

        if encounter_won and room_completed < gate.total_rooms:
            result["next_encounter"] = next_encounter

        return result
    
    def _complete_dungeon_run(self, dungeon_run: DungeonRun, user_id: str) -> Dict[str, Any]:
        """Complete a dungeon run with rewards"""
        dungeon_run.status = "completed"
        dungeon_run.completion_time = datetime.utcnow()
        dungeon_run.total_time_seconds = int((dungeon_run.completion_time - dungeon_run.start_time).total_seconds())
        
        # Calculate completion bonuses
        gate = dungeon_run.gate
        perfect_clear = dungeon_run.total_damage_taken == 0
        speed_clear = dungeon_run.total_time_seconds <= (gate.time_limit_minutes * 60 * 0.5)  # Under half time limit
        
        dungeon_run.perfect_clear = perfect_clear
        dungeon_run.speed_clear = speed_clear
        
        # Calculate final rewards
        rewards = gate.calculate_rewards(
            self.db.query(User).filter(User.id == user_id).first().level,
            dungeon_run.total_time_seconds,
            perfect_clear
        )
        
        # Apply rewards to user
        user = self.db.query(User).filter(User.id == user_id).first()
        user.add_experience(rewards["experience"])
        user.orbs += rewards["orbs"]
        user.crystals += rewards["crystals"]
        
        dungeon_run.experience_gained = rewards["experience"]
        dungeon_run.orbs_gained = rewards["orbs"]
        dungeon_run.crystals_gained = rewards["crystals"]
        
        # Update gate statistics
        gate.times_completed += 1
        total_time = gate.average_completion_time * (gate.times_completed - 1) + dungeon_run.total_time_seconds
        gate.average_completion_time = int(total_time / gate.times_completed)
        gate.success_rate = (gate.times_completed / gate.times_entered) * 100
        
        # Check achievements
        self.achievement_service.update_achievement_progress(
            user_id, "gate_clearer_achievement", 1,
            {"gate_name": gate.name, "completion_time": dungeon_run.total_time_seconds}
        )
        
        if perfect_clear:
            self.achievement_service.update_achievement_progress(
                user_id, "perfect_clear_achievement", 1,
                {"gate_name": gate.name}
            )
        
        if speed_clear:
            self.achievement_service.update_achievement_progress(
                user_id, "speed_clear_achievement", 1,
                {"gate_name": gate.name}
            )
        
        self.db.commit()
        
        return {
            "success": True,
            "message": "Dungeon completed successfully!",
            "completion_stats": {
                "total_time": dungeon_run.total_time_seconds,
                "monsters_defeated": dungeon_run.monsters_defeated,
                "boss_defeated": dungeon_run.boss_defeated,
                "accuracy": dungeon_run.questions_correct / dungeon_run.questions_answered if dungeon_run.questions_answered > 0 else 0,
                "perfect_clear": perfect_clear,
                "speed_clear": speed_clear
            },
            "rewards": rewards,
            "final_score": dungeon_run.calculate_completion_score()
        }
    
    def get_user_dungeon_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's dungeon run history"""
        runs = self.db.query(DungeonRun).filter(
            DungeonRun.user_id == user_id
        ).order_by(desc(DungeonRun.created_at)).limit(limit).all()
        
        return [
            {
                "id": str(run.id),
                "gate_name": run.gate.name if run.gate else "Unknown",
                "status": run.status,
                "completion_time": run.total_time_seconds,
                "score": run.calculate_completion_score() if run.status == "completed" else 0,
                "rewards": {
                    "experience": run.experience_gained,
                    "orbs": run.orbs_gained,
                    "crystals": run.crystals_gained
                },
                "stats": {
                    "monsters_defeated": run.monsters_defeated,
                    "boss_defeated": run.boss_defeated,
                    "accuracy": run.questions_correct / run.questions_answered if run.questions_answered > 0 else 0,
                    "perfect_clear": run.perfect_clear,
                    "speed_clear": run.speed_clear
                },
                "date": run.created_at
            }
            for run in runs
        ]
    
    def get_gate_leaderboards(self, gate_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for specific gate"""
        runs = self.db.query(DungeonRun).filter(
            and_(
                DungeonRun.gate_id == gate_id,
                DungeonRun.status == "completed"
            )
        ).order_by(desc(DungeonRun.total_time_seconds)).limit(limit).all()
        
        # Sort by score (calculated)
        scored_runs = [(run, run.calculate_completion_score()) for run in runs]
        scored_runs.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {
                "rank": i + 1,
                "user_id": str(run.user_id),
                "user_name": run.user.display_name if run.user else "Unknown",
                "score": score,
                "completion_time": run.total_time_seconds,
                "perfect_clear": run.perfect_clear,
                "speed_clear": run.speed_clear,
                "date": run.completion_time
            }
            for i, (run, score) in enumerate(scored_runs)
        ]