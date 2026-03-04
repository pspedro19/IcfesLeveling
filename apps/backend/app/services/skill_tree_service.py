"""
Skill Tree Service - ICFES Leveling
Visual Skill Tree with Nodes, Prerequisites, and Progressive Unlocking
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SkillTreeNode:
    """Represents a node in the skill tree."""

    def __init__(
        self,
        id: str,
        name: str,
        subject_id: str,
        mastery_score: float = 0.0,
        questions_seen: int = 0,
        prerequisites: List[str] = None,
        position: Dict[str, int] = None,
        tier: int = 1
    ):
        self.id = id
        self.name = name
        self.subject_id = subject_id
        self.mastery_score = mastery_score
        self.questions_seen = questions_seen
        self.prerequisites = prerequisites or []
        self.position = position or {"x": 0, "y": 0}
        self.tier = tier

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "subject_id": self.subject_id,
            "mastery_score": self.mastery_score,
            "questions_seen": self.questions_seen,
            "prerequisites": self.prerequisites,
            "position": self.position,
            "tier": self.tier,
            "status": self._get_status(),
            "is_unlocked": self._is_unlocked(),
            "can_level_up": self._can_level_up()
        }

    def _get_status(self) -> str:
        """Get node status based on mastery score."""
        if self.mastery_score >= 0.8:
            return "mastered"
        elif self.mastery_score >= 0.6:
            return "strong"
        elif self.mastery_score >= 0.4:
            return "learning"
        elif self.mastery_score > 0:
            return "weak"
        else:
            return "locked"

    def _is_unlocked(self) -> bool:
        """Check if node is unlocked (no prerequisites or all prerequisites met)."""
        # For now, return True if mastery > 0 or no prerequisites
        return self.mastery_score > 0 or len(self.prerequisites) == 0

    def _can_level_up(self) -> bool:
        """Check if node can level up (close to next threshold)."""
        thresholds = [0.4, 0.6, 0.8, 1.0]
        for threshold in thresholds:
            if self.mastery_score < threshold and self.mastery_score >= threshold - 0.1:
                return True
        return False


class SkillTreeService:
    """Service for managing skill tree visualization and progression."""

    # Default topic relationships (prerequisites)
    TOPIC_PREREQUISITES = {
        # Mathematics
        "algebra_basica": [],
        "ecuaciones_lineales": ["algebra_basica"],
        "sistemas_ecuaciones": ["ecuaciones_lineales"],
        "funciones": ["ecuaciones_lineales"],
        "funciones_cuadraticas": ["funciones"],
        "trigonometria": ["funciones"],
        "calculo_diferencial": ["funciones", "trigonometria"],
        "estadistica_basica": ["algebra_basica"],
        "probabilidad": ["estadistica_basica"],
        "geometria_basica": [],
        "geometria_analitica": ["geometria_basica", "algebra_basica"],

        # Lectura Critica
        "comprension_literal": [],
        "comprension_inferencial": ["comprension_literal"],
        "comprension_critica": ["comprension_inferencial"],
        "analisis_textual": ["comprension_critica"],
        "argumentacion": ["analisis_textual"],

        # Ciencias Naturales
        "fisica_mecanica": [],
        "cinematica": ["fisica_mecanica"],
        "dinamica": ["cinematica"],
        "energia": ["dinamica"],
        "ondas": ["fisica_mecanica"],
        "quimica_basica": [],
        "estequiometria": ["quimica_basica"],
        "quimica_organica": ["estequiometria"],
        "biologia_celular": [],
        "genetica": ["biologia_celular"],
        "ecologia": ["biologia_celular"],
    }

    def __init__(self, db: Session):
        self.db = db

    def get_skill_tree(self, user_id: UUID, subject_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get complete skill tree for a user.
        Returns nodes with connections for visual rendering.
        """
        try:
            # Get all topics with user mastery
            query = text("""
                SELECT
                    t.id,
                    t.name,
                    t.subject_id,
                    s.name as subject_name,
                    COALESCE(utm.mastery_score, 0) as mastery_score,
                    COALESCE(utm.questions_seen, 0) as questions_seen,
                    COALESCE(utm.questions_correct, 0) as questions_correct,
                    t.display_order,
                    t.codigo_tema
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN user_topic_mastery utm ON utm.topic_id = t.id AND utm.user_id = :user_id
                WHERE (:subject_id IS NULL OR t.subject_id = :subject_id)
                ORDER BY s.name, t.display_order, t.name
            """)

            result = self.db.execute(query, {
                "user_id": str(user_id),
                "subject_id": subject_id
            }).fetchall()

            # Group by subject
            subjects = {}
            for row in result:
                subj_id = str(row[2])
                if subj_id not in subjects:
                    subjects[subj_id] = {
                        "id": subj_id,
                        "name": row[3],
                        "nodes": [],
                        "connections": []
                    }

                # Create node
                topic_code = row[8] if row[8] else self._normalize_topic_name(row[1])
                prerequisites = self.TOPIC_PREREQUISITES.get(topic_code, [])

                # Calculate position based on tier (prerequisites count)
                tier = len(prerequisites) + 1
                display_order = row[7] if row[7] else len(subjects[subj_id]["nodes"])

                node = SkillTreeNode(
                    id=str(row[0]),
                    name=row[1],
                    subject_id=subj_id,
                    mastery_score=float(row[4]) if row[4] else 0.0,
                    questions_seen=int(row[5]) if row[5] else 0,
                    prerequisites=prerequisites,
                    position={
                        "x": display_order % 4,  # 4 columns
                        "y": tier - 1  # Row based on tier
                    },
                    tier=tier
                )

                subjects[subj_id]["nodes"].append(node.to_dict())

            # Build connections
            for subj_id, subj_data in subjects.items():
                connections = self._build_connections(subj_data["nodes"])
                subjects[subj_id]["connections"] = connections

            # Calculate subject-level stats
            subject_stats = []
            for subj_id, subj_data in subjects.items():
                nodes = subj_data["nodes"]
                total_nodes = len(nodes)
                mastered_nodes = sum(1 for n in nodes if n["status"] == "mastered")
                strong_nodes = sum(1 for n in nodes if n["status"] == "strong")
                avg_mastery = sum(n["mastery_score"] for n in nodes) / max(total_nodes, 1)

                subject_stats.append({
                    "subject_id": subj_id,
                    "subject_name": subj_data["name"],
                    "total_nodes": total_nodes,
                    "mastered_nodes": mastered_nodes,
                    "strong_nodes": strong_nodes,
                    "average_mastery": round(avg_mastery * 100, 1),
                    "completion_percentage": round((mastered_nodes + strong_nodes) / max(total_nodes, 1) * 100, 1)
                })

            return {
                "subjects": list(subjects.values()),
                "subject_stats": subject_stats,
                "total_nodes": sum(len(s["nodes"]) for s in subjects.values()),
                "total_mastered": sum(ss["mastered_nodes"] for ss in subject_stats)
            }

        except Exception as e:
            logger.error(f"Error getting skill tree: {e}")
            return self._get_default_skill_tree()

    def _normalize_topic_name(self, name: str) -> str:
        """Normalize topic name to match prerequisites keys."""
        import re
        # Remove accents, lowercase, replace spaces with underscores
        normalized = name.lower()
        normalized = re.sub(r'[áàäâ]', 'a', normalized)
        normalized = re.sub(r'[éèëê]', 'e', normalized)
        normalized = re.sub(r'[íìïî]', 'i', normalized)
        normalized = re.sub(r'[óòöô]', 'o', normalized)
        normalized = re.sub(r'[úùüû]', 'u', normalized)
        normalized = re.sub(r'[ñ]', 'n', normalized)
        normalized = re.sub(r'\s+', '_', normalized)
        normalized = re.sub(r'[^a-z0-9_]', '', normalized)
        return normalized

    def _build_connections(self, nodes: List[Dict]) -> List[Dict]:
        """Build connections between nodes based on prerequisites."""
        connections = []
        node_map = {self._normalize_topic_name(n["name"]): n["id"] for n in nodes}

        for node in nodes:
            for prereq in node.get("prerequisites", []):
                if prereq in node_map:
                    connections.append({
                        "from": node_map[prereq],
                        "to": node["id"],
                        "type": "prerequisite"
                    })

        return connections

    def _get_default_skill_tree(self) -> Dict[str, Any]:
        """Return default skill tree structure when database query fails."""
        return {
            "subjects": [],
            "subject_stats": [],
            "total_nodes": 0,
            "total_mastered": 0
        }

    def check_level_up(self, user_id: UUID, topic_id: str, new_mastery: float) -> Optional[Dict[str, Any]]:
        """
        Check if user leveled up in a topic and return level-up data.
        """
        try:
            # Get previous mastery
            query = text("""
                SELECT mastery_score FROM user_topic_mastery
                WHERE user_id = :user_id AND topic_id = :topic_id
            """)

            result = self.db.execute(query, {
                "user_id": str(user_id),
                "topic_id": topic_id
            }).fetchone()

            old_mastery = float(result[0]) if result else 0.0

            # Define level thresholds
            thresholds = [
                (0.0, "locked", "Bloqueado"),
                (0.2, "weak", "Debil"),
                (0.4, "learning", "Aprendiendo"),
                (0.6, "strong", "Fuerte"),
                (0.8, "mastered", "Maestro")
            ]

            old_level = None
            new_level = None

            for threshold, status, name in thresholds:
                if old_mastery >= threshold:
                    old_level = (threshold, status, name)
                if new_mastery >= threshold:
                    new_level = (threshold, status, name)

            # Check if level changed
            if new_level and old_level and new_level[0] > old_level[0]:
                return {
                    "leveled_up": True,
                    "topic_id": topic_id,
                    "old_level": old_level[1],
                    "new_level": new_level[1],
                    "old_level_name": old_level[2],
                    "new_level_name": new_level[2],
                    "old_mastery": round(old_mastery * 100, 1),
                    "new_mastery": round(new_mastery * 100, 1),
                    "xp_bonus": self._get_level_up_xp(new_level[1])
                }

            return None

        except Exception as e:
            logger.error(f"Error checking level up: {e}")
            return None

    def _get_level_up_xp(self, new_level: str) -> int:
        """Get XP bonus for reaching a new level."""
        xp_rewards = {
            "weak": 10,
            "learning": 25,
            "strong": 50,
            "mastered": 100
        }
        return xp_rewards.get(new_level, 0)

    def get_unlockable_nodes(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get nodes that are close to being unlocked or leveled up.
        Used for showing progress opportunities to users.
        """
        try:
            query = text("""
                SELECT
                    t.id,
                    t.name,
                    t.subject_id,
                    s.name as subject_name,
                    COALESCE(utm.mastery_score, 0) as mastery_score
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN user_topic_mastery utm ON utm.topic_id = t.id AND utm.user_id = :user_id
                WHERE utm.mastery_score IS NULL
                   OR (utm.mastery_score >= 0.35 AND utm.mastery_score < 0.4)
                   OR (utm.mastery_score >= 0.55 AND utm.mastery_score < 0.6)
                   OR (utm.mastery_score >= 0.75 AND utm.mastery_score < 0.8)
                ORDER BY utm.mastery_score DESC NULLS LAST
                LIMIT 10
            """)

            result = self.db.execute(query, {"user_id": str(user_id)}).fetchall()

            unlockable = []
            for row in result:
                mastery = float(row[4]) if row[4] else 0
                next_threshold = self._get_next_threshold(mastery)

                unlockable.append({
                    "topic_id": str(row[0]),
                    "topic_name": row[1],
                    "subject_id": str(row[2]),
                    "subject_name": row[3],
                    "current_mastery": round(mastery * 100, 1),
                    "next_threshold": round(next_threshold * 100, 1),
                    "progress_to_next": round((mastery / next_threshold) * 100, 1) if next_threshold > 0 else 100,
                    "questions_needed": self._estimate_questions_to_unlock(mastery, next_threshold)
                })

            return unlockable

        except Exception as e:
            logger.error(f"Error getting unlockable nodes: {e}")
            return []

    def _get_next_threshold(self, current: float) -> float:
        """Get next level threshold."""
        thresholds = [0.2, 0.4, 0.6, 0.8, 1.0]
        for t in thresholds:
            if current < t:
                return t
        return 1.0

    def _estimate_questions_to_unlock(self, current: float, target: float) -> int:
        """Estimate questions needed to reach next threshold."""
        if current >= target:
            return 0
        # Rough estimate: each correct question adds ~0.05 mastery
        diff = target - current
        return max(1, int(diff / 0.05))
