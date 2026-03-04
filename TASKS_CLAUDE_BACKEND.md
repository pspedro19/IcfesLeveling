# TAREAS PARA CLAUDE CODE: Backend y APIs

**Proyecto:** ICFES Leveling - Modo Conquista
**Responsable:** Claude Code (Backend Developer)
**Stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, WebSocket
**Fecha:** 29 de Diciembre, 2025

---

## Resumen de Entregables

| Categoria | Cantidad | Prioridad | Ubicacion |
|-----------|----------|-----------|-----------|
| Nuevas Tablas SQL | 6 tablas | CRITICA | `apps/backend/` |
| Nuevos Servicios | 5 servicios | CRITICA | `apps/backend/app/services/` |
| Nuevos Endpoints | 15+ endpoints | ALTA | `apps/backend/app/routes/` |
| Modificaciones | 3 archivos | CRITICA | Varios |
| Nuevos Schemas | 8 schemas | ALTA | `apps/backend/app/schemas/` |

---

## FASE 1: CRITICA (Dias 1-3)

### TAREA 1.1: Modificar DungeonService para incluir Explicaciones

**Prioridad:** CRITICA
**Archivo:** `apps/backend/app/services/dungeon_service.py`
**Impacto:** Sin explicaciones, no hay aprendizaje real

#### Modificacion Requerida

Buscar la funcion que procesa respuestas y agregar el campo `explanation`:

```python
# dungeon_service.py

def submit_encounter_answer(
    self,
    db: Session,
    user_id: str,
    encounter_id: str,
    question_id: str,
    answer_id: str,
    time_spent_seconds: int
) -> dict:
    """
    Procesa una respuesta del usuario y calcula el resultado del combate.
    MODIFICACION: Ahora incluye explanation y video_url en la respuesta.
    """
    # Obtener la pregunta con su explicacion
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verificar respuesta
    is_correct = question.correct_answer == answer_id

    # Obtener el encounter y run actuales
    encounter = db.query(DungeonEncounter).filter(
        DungeonEncounter.id == encounter_id
    ).first()
    run = db.query(DungeonRun).filter(
        DungeonRun.id == encounter.dungeon_run_id
    ).first()

    # Calcular dano
    BASE_PLAYER_DAMAGE = 50
    BASE_ENEMY_DAMAGE = 20

    if is_correct:
        # Bonus por velocidad (max 30% si responde en menos de 10s)
        speed_bonus = max(0, (30 - time_spent_seconds) / 30) * 0.3
        # Bonus por combo (5% por cada combo, max 50%)
        combo_bonus = min(run.current_combo * 0.05, 0.5)

        damage_to_enemy = int(BASE_PLAYER_DAMAGE * (1 + speed_bonus + combo_bonus))
        damage_to_player = 0
        new_combo = run.current_combo + 1
        xp_earned = int(question.xp_value * (1 + combo_bonus))
    else:
        damage_to_enemy = 0
        damage_to_player = BASE_ENEMY_DAMAGE
        new_combo = 0
        xp_earned = 0

    # Actualizar HP
    encounter.enemy_current_hp = max(0, encounter.enemy_current_hp - damage_to_enemy)
    run.player_current_hp = max(0, run.player_current_hp - damage_to_player)
    run.current_combo = new_combo
    run.total_xp_earned += xp_earned

    # Verificar fin de batalla
    enemy_defeated = encounter.enemy_current_hp <= 0
    player_defeated = run.player_current_hp <= 0

    db.commit()

    # RESPUESTA CON EXPLICACION (NUEVO)
    return {
        "correct": is_correct,
        "correct_answer_id": question.correct_answer,
        "explanation": question.explanation,  # <-- CRITICO
        "video_url": getattr(question, 'video_url', None),  # <-- OPCIONAL
        "damage_dealt": damage_to_enemy,
        "damage_taken": damage_to_player,
        "enemy_current_hp": encounter.enemy_current_hp,
        "player_current_hp": run.player_current_hp,
        "current_combo": new_combo,
        "xp_earned": xp_earned,
        "enemy_defeated": enemy_defeated,
        "player_defeated": player_defeated,
        "encounter_completed": enemy_defeated or player_defeated
    }
```

#### Verificar que el modelo Question tenga explanation

```python
# models/question.py o donde este definido
class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID, primary_key=True)
    text = Column(Text, nullable=False)
    correct_answer = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=True)  # <-- Verificar que exista
    video_url = Column(String(500), nullable=True)  # <-- Agregar si no existe
    xp_value = Column(Integer, default=10)
    # ... otros campos
```

---

### TAREA 1.2: Crear Tabla y Servicio de Corazones (Hearts)

**Prioridad:** CRITICA
**Archivos a crear:**
- `apps/backend/app/models/hearts.py`
- `apps/backend/app/services/hearts_service.py`
- `apps/backend/app/routes/hearts.py`
- `apps/backend/app/schemas/hearts.py`

#### 1.2.1 Modelo SQL

```python
# apps/backend/app/models/hearts.py

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class UserHearts(Base):
    __tablename__ = "user_hearts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    current_hearts = Column(Integer, default=5, nullable=False)
    max_hearts = Column(Integer, default=5, nullable=False)
    last_heart_lost_at = Column(DateTime(timezone=True), nullable=True)
    last_regen_at = Column(DateTime(timezone=True), server_default=func.now())
    is_grace_mode = Column(Boolean, default=False, nullable=False)
    ads_watched_today = Column(Integer, default=0, nullable=False)
    last_ad_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Constantes
    REGEN_HOURS = 4  # 1 corazon cada 4 horas
    MAX_ADS_PER_DAY = 3
```

#### 1.2.2 Servicio de Corazones

```python
# apps/backend/app/services/hearts_service.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.hearts import UserHearts
from fastapi import HTTPException
from typing import Optional
import uuid

class HeartsService:
    REGEN_HOURS = 4
    MAX_HEARTS = 5
    MAX_ADS_PER_DAY = 3
    REFILL_COST_GOLD = 150

    def get_user_hearts(self, db: Session, user_id: str) -> UserHearts:
        """Obtiene o crea el registro de corazones del usuario"""
        hearts = db.query(UserHearts).filter(
            UserHearts.user_id == uuid.UUID(user_id)
        ).first()

        if not hearts:
            hearts = UserHearts(
                user_id=uuid.UUID(user_id),
                current_hearts=self.MAX_HEARTS,
                max_hearts=self.MAX_HEARTS
            )
            db.add(hearts)
            db.commit()
            db.refresh(hearts)

        # Aplicar regeneracion automatica
        self._apply_regeneration(db, hearts)

        return hearts

    def _apply_regeneration(self, db: Session, hearts: UserHearts) -> None:
        """Regenera corazones basado en tiempo transcurrido"""
        if hearts.current_hearts >= hearts.max_hearts:
            return

        if not hearts.last_heart_lost_at:
            return

        now = datetime.utcnow()
        time_since_loss = now - hearts.last_heart_lost_at
        hours_passed = time_since_loss.total_seconds() / 3600

        hearts_to_regen = int(hours_passed / self.REGEN_HOURS)

        if hearts_to_regen > 0:
            hearts.current_hearts = min(
                hearts.max_hearts,
                hearts.current_hearts + hearts_to_regen
            )
            hearts.last_regen_at = now

            if hearts.current_hearts >= hearts.max_hearts:
                hearts.last_heart_lost_at = None

            db.commit()

    def lose_heart(self, db: Session, user_id: str) -> dict:
        """Pierde un corazon. Retorna estado actualizado."""
        hearts = self.get_user_hearts(db, user_id)

        if hearts.is_grace_mode:
            return {
                "hearts_remaining": hearts.current_hearts,
                "is_grace_mode": True,
                "message": "Grace mode active - no heart lost"
            }

        if hearts.current_hearts > 0:
            hearts.current_hearts -= 1
            hearts.last_heart_lost_at = datetime.utcnow()
            db.commit()

        return {
            "hearts_remaining": hearts.current_hearts,
            "is_grace_mode": hearts.is_grace_mode,
            "next_regen_in_seconds": self._get_next_regen_seconds(hearts),
            "can_watch_ad": self._can_watch_ad(hearts),
            "message": "Heart lost" if hearts.current_hearts > 0 else "No hearts remaining"
        }

    def _get_next_regen_seconds(self, hearts: UserHearts) -> Optional[int]:
        """Calcula segundos hasta la proxima regeneracion"""
        if hearts.current_hearts >= hearts.max_hearts:
            return None

        if not hearts.last_heart_lost_at:
            return None

        next_regen = hearts.last_heart_lost_at + timedelta(hours=self.REGEN_HOURS)
        remaining = (next_regen - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

    def _can_watch_ad(self, hearts: UserHearts) -> bool:
        """Verifica si puede ver un anuncio para recuperar corazon"""
        today = datetime.utcnow().date()

        if hearts.last_ad_date and hearts.last_ad_date.date() == today:
            return hearts.ads_watched_today < self.MAX_ADS_PER_DAY

        return True

    def restore_heart_with_ad(self, db: Session, user_id: str) -> dict:
        """Restaura 1 corazon despues de ver anuncio"""
        hearts = self.get_user_hearts(db, user_id)

        if not self._can_watch_ad(hearts):
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {self.MAX_ADS_PER_DAY} ads per day reached"
            )

        if hearts.current_hearts >= hearts.max_hearts:
            raise HTTPException(
                status_code=400,
                detail="Hearts already full"
            )

        today = datetime.utcnow().date()
        if not hearts.last_ad_date or hearts.last_ad_date.date() != today:
            hearts.ads_watched_today = 0

        hearts.current_hearts += 1
        hearts.ads_watched_today += 1
        hearts.last_ad_date = datetime.utcnow()
        db.commit()

        return {
            "hearts_remaining": hearts.current_hearts,
            "ads_remaining_today": self.MAX_ADS_PER_DAY - hearts.ads_watched_today
        }

    def refill_hearts_with_gold(self, db: Session, user_id: str) -> dict:
        """Recarga todos los corazones usando oro"""
        from app.services.economy_service import EconomyService

        economy_service = EconomyService()
        hearts = self.get_user_hearts(db, user_id)

        if hearts.current_hearts >= hearts.max_hearts:
            raise HTTPException(
                status_code=400,
                detail="Hearts already full"
            )

        # Deducir oro
        economy_service.spend_gold(db, user_id, self.REFILL_COST_GOLD, "heart_refill")

        hearts.current_hearts = hearts.max_hearts
        hearts.last_heart_lost_at = None
        db.commit()

        return {
            "hearts_remaining": hearts.current_hearts,
            "gold_spent": self.REFILL_COST_GOLD
        }

    def enter_grace_mode(self, db: Session, user_id: str) -> dict:
        """Activa el modo gracia (practica sin recompensas)"""
        hearts = self.get_user_hearts(db, user_id)
        hearts.is_grace_mode = True
        db.commit()

        return {
            "is_grace_mode": True,
            "message": "Grace mode activated. You can practice without earning XP or Gold."
        }

    def exit_grace_mode(self, db: Session, user_id: str) -> dict:
        """Desactiva el modo gracia"""
        hearts = self.get_user_hearts(db, user_id)
        hearts.is_grace_mode = False
        db.commit()

        return {
            "is_grace_mode": False,
            "hearts_remaining": hearts.current_hearts
        }


hearts_service = HeartsService()
```

#### 1.2.3 Endpoints de Corazones

```python
# apps/backend/app/routes/hearts.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.hearts_service import hearts_service
from app.schemas.hearts import (
    HeartsStatusResponse,
    HeartActionResponse
)

router = APIRouter(prefix="/hearts", tags=["Hearts"])


@router.get("/status", response_model=HeartsStatusResponse)
async def get_hearts_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el estado actual de corazones del usuario"""
    hearts = hearts_service.get_user_hearts(db, str(current_user.id))
    return {
        "current_hearts": hearts.current_hearts,
        "max_hearts": hearts.max_hearts,
        "is_grace_mode": hearts.is_grace_mode,
        "next_regen_in_seconds": hearts_service._get_next_regen_seconds(hearts),
        "can_watch_ad": hearts_service._can_watch_ad(hearts),
        "ads_remaining_today": hearts_service.MAX_ADS_PER_DAY - hearts.ads_watched_today
    }


@router.post("/restore-with-ad", response_model=HeartActionResponse)
async def restore_heart_with_ad(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restaura 1 corazon despues de ver anuncio"""
    return hearts_service.restore_heart_with_ad(db, str(current_user.id))


@router.post("/refill-with-gold", response_model=HeartActionResponse)
async def refill_hearts_with_gold(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recarga todos los corazones usando 150 oro"""
    return hearts_service.refill_hearts_with_gold(db, str(current_user.id))


@router.post("/grace-mode/enter")
async def enter_grace_mode(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activa el modo gracia"""
    return hearts_service.enter_grace_mode(db, str(current_user.id))


@router.post("/grace-mode/exit")
async def exit_grace_mode(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Desactiva el modo gracia"""
    return hearts_service.exit_grace_mode(db, str(current_user.id))
```

#### 1.2.4 Schemas

```python
# apps/backend/app/schemas/hearts.py

from pydantic import BaseModel
from typing import Optional

class HeartsStatusResponse(BaseModel):
    current_hearts: int
    max_hearts: int
    is_grace_mode: bool
    next_regen_in_seconds: Optional[int]
    can_watch_ad: bool
    ads_remaining_today: int

class HeartActionResponse(BaseModel):
    hearts_remaining: int
    is_grace_mode: Optional[bool] = None
    ads_remaining_today: Optional[int] = None
    gold_spent: Optional[int] = None
    message: Optional[str] = None
```

---

### TAREA 1.3: Crear Tabla y Servicio de Economia

**Prioridad:** CRITICA
**Archivos a crear:**
- `apps/backend/app/models/economy.py`
- `apps/backend/app/services/economy_service.py`
- `apps/backend/app/routes/economy.py`
- `apps/backend/app/schemas/economy.py`

#### 1.3.1 Modelo SQL

```python
# apps/backend/app/models/economy.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class UserEconomy(Base):
    __tablename__ = "user_economy"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    gold = Column(Integer, default=100, nullable=False)  # Oro inicial de bienvenida
    total_xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    rank = Column(String(10), default='E', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GoldTransaction(Base):
    __tablename__ = "gold_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Positivo = ganado, Negativo = gastado
    transaction_type = Column(String(50), nullable=False)  # 'battle_win', 'streak_bonus', 'purchase', etc.
    description = Column(Text, nullable=True)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class XPTransaction(Base):
    __tablename__ = "xp_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)  # 'battle', 'combo_bonus', 'streak_bonus', etc.
    level_before = Column(Integer, nullable=False)
    level_after = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 1.3.2 Servicio de Economia

```python
# apps/backend/app/services/economy_service.py

from sqlalchemy.orm import Session
from app.models.economy import UserEconomy, GoldTransaction, XPTransaction
from fastapi import HTTPException
import uuid
import math

class EconomyService:

    # Tabla de rangos
    RANKS = [
        ('E', 0, 0.35),      # 0-35% mastery
        ('D', 0.35, 0.50),   # 35-50%
        ('C', 0.50, 0.65),   # 50-65%
        ('B', 0.65, 0.80),   # 65-80%
        ('A', 0.80, 0.90),   # 80-90%
        ('S', 0.90, 1.00),   # 90-100%
    ]

    def get_user_economy(self, db: Session, user_id: str) -> UserEconomy:
        """Obtiene o crea la economia del usuario"""
        economy = db.query(UserEconomy).filter(
            UserEconomy.user_id == uuid.UUID(user_id)
        ).first()

        if not economy:
            economy = UserEconomy(
                user_id=uuid.UUID(user_id),
                gold=100,  # Bienvenida
                total_xp=0,
                level=1,
                rank='E'
            )
            db.add(economy)
            db.commit()
            db.refresh(economy)

        return economy

    def add_gold(
        self,
        db: Session,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str = None
    ) -> dict:
        """Agrega oro al usuario"""
        economy = self.get_user_economy(db, user_id)
        economy.gold += amount

        # Registrar transaccion
        transaction = GoldTransaction(
            user_id=uuid.UUID(user_id),
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            balance_after=economy.gold
        )
        db.add(transaction)
        db.commit()

        return {
            "gold_added": amount,
            "new_balance": economy.gold,
            "transaction_type": transaction_type
        }

    def spend_gold(
        self,
        db: Session,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str = None
    ) -> dict:
        """Gasta oro del usuario"""
        economy = self.get_user_economy(db, user_id)

        if economy.gold < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient gold. Have: {economy.gold}, Need: {amount}"
            )

        economy.gold -= amount

        # Registrar transaccion
        transaction = GoldTransaction(
            user_id=uuid.UUID(user_id),
            amount=-amount,
            transaction_type=transaction_type,
            description=description,
            balance_after=economy.gold
        )
        db.add(transaction)
        db.commit()

        return {
            "gold_spent": amount,
            "new_balance": economy.gold,
            "transaction_type": transaction_type
        }

    def add_xp(
        self,
        db: Session,
        user_id: str,
        amount: int,
        source: str
    ) -> dict:
        """Agrega XP y verifica subida de nivel"""
        economy = self.get_user_economy(db, user_id)

        level_before = economy.level
        economy.total_xp += amount
        new_level = self._calculate_level(economy.total_xp)

        leveled_up = new_level > level_before
        if leveled_up:
            economy.level = new_level
            # Bonus de oro por subir de nivel
            self.add_gold(db, user_id, 25, "level_up", f"Level up to {new_level}")

        # Registrar transaccion XP
        transaction = XPTransaction(
            user_id=uuid.UUID(user_id),
            amount=amount,
            source=source,
            level_before=level_before,
            level_after=new_level
        )
        db.add(transaction)
        db.commit()

        return {
            "xp_added": amount,
            "total_xp": economy.total_xp,
            "level": economy.level,
            "leveled_up": leveled_up,
            "xp_to_next_level": self._xp_for_next_level(economy.level, economy.total_xp)
        }

    def _calculate_level(self, total_xp: int) -> int:
        """Calcula el nivel basado en XP total"""
        # Formula: XP requerido = 100 * nivel^1.5
        level = 1
        xp_accumulated = 0

        while True:
            xp_for_next = int(100 * (level ** 1.5))
            if xp_accumulated + xp_for_next > total_xp:
                break
            xp_accumulated += xp_for_next
            level += 1

        return level

    def _xp_for_next_level(self, current_level: int, total_xp: int) -> int:
        """XP faltante para el siguiente nivel"""
        xp_accumulated = 0
        for lvl in range(1, current_level):
            xp_accumulated += int(100 * (lvl ** 1.5))

        xp_for_current = int(100 * (current_level ** 1.5))
        xp_in_current_level = total_xp - xp_accumulated

        return xp_for_current - xp_in_current_level

    def update_rank(self, db: Session, user_id: str, mastery_percent: float) -> dict:
        """Actualiza el rango basado en mastery global"""
        economy = self.get_user_economy(db, user_id)
        old_rank = economy.rank

        new_rank = 'E'
        for rank, min_mastery, max_mastery in self.RANKS:
            if min_mastery <= mastery_percent < max_mastery:
                new_rank = rank
                break
            if mastery_percent >= 0.90:
                new_rank = 'S'

        rank_changed = new_rank != old_rank
        if rank_changed:
            economy.rank = new_rank
            # Bonus por subir de rango
            rank_bonus = {'E': 0, 'D': 50, 'C': 75, 'B': 100, 'A': 150, 'S': 200}
            if rank_bonus.get(new_rank, 0) > rank_bonus.get(old_rank, 0):
                self.add_gold(
                    db, user_id,
                    rank_bonus[new_rank] - rank_bonus.get(old_rank, 0),
                    "rank_up",
                    f"Rank up from {old_rank} to {new_rank}"
                )

            db.commit()

        return {
            "old_rank": old_rank,
            "new_rank": new_rank,
            "rank_changed": rank_changed
        }


economy_service = EconomyService()
```

#### 1.3.3 Endpoints de Economia

```python
# apps/backend/app/routes/economy.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.economy_service import economy_service
from app.schemas.economy import EconomyStatusResponse, GoldTransactionResponse

router = APIRouter(prefix="/economy", tags=["Economy"])


@router.get("/status", response_model=EconomyStatusResponse)
async def get_economy_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el estado economico del usuario"""
    economy = economy_service.get_user_economy(db, str(current_user.id))
    return {
        "gold": economy.gold,
        "total_xp": economy.total_xp,
        "level": economy.level,
        "rank": economy.rank,
        "xp_to_next_level": economy_service._xp_for_next_level(
            economy.level, economy.total_xp
        )
    }


@router.get("/transactions/gold")
async def get_gold_transactions(
    limit: int = 20,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene historial de transacciones de oro"""
    from app.models.economy import GoldTransaction
    import uuid

    transactions = db.query(GoldTransaction).filter(
        GoldTransaction.user_id == uuid.UUID(str(current_user.id))
    ).order_by(GoldTransaction.created_at.desc()).limit(limit).all()

    return [
        {
            "amount": t.amount,
            "type": t.transaction_type,
            "description": t.description,
            "balance_after": t.balance_after,
            "created_at": t.created_at.isoformat()
        }
        for t in transactions
    ]
```

---

## FASE 2: ALTA (Dias 4-7)

### TAREA 2.1: Crear Sistema de Rachas (Streaks)

**Prioridad:** ALTA
**Archivos a crear:**
- `apps/backend/app/models/streaks.py`
- `apps/backend/app/services/streak_service.py`
- `apps/backend/app/routes/streaks.py`

#### 2.1.1 Modelo SQL

```python
# apps/backend/app/models/streaks.py

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class UserStreak(Base):
    __tablename__ = "user_streaks"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(Date, nullable=True)
    streak_multiplier = Column(DECIMAL(3, 2), default=1.00, nullable=False)
    freeze_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 2.1.2 Servicio de Rachas

```python
# apps/backend/app/services/streak_service.py

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.streaks import UserStreak
from app.services.economy_service import economy_service
from fastapi import HTTPException
from decimal import Decimal
import uuid

class StreakService:
    MIN_XP_FOR_STREAK = 20  # XP minimo para mantener racha
    RESET_HOUR = 4  # 4 AM reset

    MULTIPLIERS = {
        7: Decimal('1.20'),   # 7 dias = 1.2x
        14: Decimal('1.30'),  # 14 dias = 1.3x
        30: Decimal('1.50'),  # 30 dias = 1.5x
        60: Decimal('1.80'),  # 60+ dias = 1.8x
    }

    FREEZE_COST = 200  # Oro
    REPAIR_COST = 300  # Oro

    def get_user_streak(self, db: Session, user_id: str) -> UserStreak:
        """Obtiene o crea el registro de racha del usuario"""
        streak = db.query(UserStreak).filter(
            UserStreak.user_id == uuid.UUID(user_id)
        ).first()

        if not streak:
            streak = UserStreak(
                user_id=uuid.UUID(user_id),
                current_streak=0,
                longest_streak=0,
                streak_multiplier=Decimal('1.00')
            )
            db.add(streak)
            db.commit()
            db.refresh(streak)

        return streak

    def check_and_update_streak(self, db: Session, user_id: str, xp_earned: int) -> dict:
        """Verifica y actualiza la racha despues de practicar"""
        streak = self.get_user_streak(db, user_id)
        today = date.today()

        # Si ya practico hoy, no hacer nada
        if streak.last_activity_date == today:
            return {
                "current_streak": streak.current_streak,
                "streak_maintained": False,
                "message": "Already practiced today"
            }

        yesterday = today - timedelta(days=1)

        # Verificar si mantiene la racha
        if streak.last_activity_date == yesterday:
            # Racha continua
            if xp_earned >= self.MIN_XP_FOR_STREAK:
                streak.current_streak += 1
                streak.last_activity_date = today
                streak.streak_multiplier = self._calculate_multiplier(streak.current_streak)

                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak

                # Bonus de oro por racha
                economy_service.add_gold(
                    db, user_id, 5, "streak_bonus",
                    f"Streak day {streak.current_streak}"
                )

                db.commit()

                return {
                    "current_streak": streak.current_streak,
                    "streak_maintained": True,
                    "multiplier": float(streak.streak_multiplier),
                    "message": f"Streak extended to {streak.current_streak} days!"
                }

        elif streak.last_activity_date and streak.last_activity_date < yesterday:
            # Racha perdida (a menos que tenga freeze)
            if streak.freeze_count > 0:
                streak.freeze_count -= 1
                streak.last_activity_date = today
                db.commit()

                return {
                    "current_streak": streak.current_streak,
                    "streak_maintained": True,
                    "freeze_used": True,
                    "freezes_remaining": streak.freeze_count,
                    "message": "Streak freeze used!"
                }
            else:
                # Perder racha
                old_streak = streak.current_streak
                streak.current_streak = 1 if xp_earned >= self.MIN_XP_FOR_STREAK else 0
                streak.streak_multiplier = Decimal('1.00')
                streak.last_activity_date = today if xp_earned >= self.MIN_XP_FOR_STREAK else None
                db.commit()

                return {
                    "current_streak": streak.current_streak,
                    "streak_lost": True,
                    "previous_streak": old_streak,
                    "message": "Streak lost, but you can rebuild!"
                }

        else:
            # Primera vez o sin actividad previa
            if xp_earned >= self.MIN_XP_FOR_STREAK:
                streak.current_streak = 1
                streak.last_activity_date = today
                db.commit()

                return {
                    "current_streak": 1,
                    "streak_started": True,
                    "message": "Streak started!"
                }

        return {"current_streak": streak.current_streak}

    def _calculate_multiplier(self, streak_days: int) -> Decimal:
        """Calcula el multiplicador basado en dias de racha"""
        multiplier = Decimal('1.00')
        for days, mult in sorted(self.MULTIPLIERS.items()):
            if streak_days >= days:
                multiplier = mult
        return multiplier

    def buy_streak_freeze(self, db: Session, user_id: str) -> dict:
        """Compra un streak freeze con oro"""
        streak = self.get_user_streak(db, user_id)

        if streak.freeze_count >= 5:
            raise HTTPException(
                status_code=400,
                detail="Maximum 5 freezes allowed"
            )

        economy_service.spend_gold(db, user_id, self.FREEZE_COST, "streak_freeze")
        streak.freeze_count += 1
        db.commit()

        return {
            "freeze_count": streak.freeze_count,
            "gold_spent": self.FREEZE_COST
        }

    def repair_streak(self, db: Session, user_id: str) -> dict:
        """Repara una racha perdida (ventana de 24h)"""
        streak = self.get_user_streak(db, user_id)
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Solo puede reparar si perdio ayer
        if streak.last_activity_date and streak.last_activity_date < yesterday:
            days_missed = (today - streak.last_activity_date).days
            if days_missed > 2:
                raise HTTPException(
                    status_code=400,
                    detail="Repair window expired (24h max)"
                )

        economy_service.spend_gold(db, user_id, self.REPAIR_COST, "streak_repair")

        # Restaurar racha
        streak.last_activity_date = today
        db.commit()

        return {
            "current_streak": streak.current_streak,
            "streak_repaired": True,
            "gold_spent": self.REPAIR_COST
        }


streak_service = StreakService()
```

---

### TAREA 2.2: Crear Sistema de Progreso por Nodo

**Prioridad:** ALTA
**Archivos a crear:**
- `apps/backend/app/models/node_progress.py`
- `apps/backend/app/services/node_progress_service.py`

#### 2.2.1 Modelo SQL

```python
# apps/backend/app/models/node_progress.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class UserKingdomProgress(Base):
    __tablename__ = "user_kingdom_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    kingdom_id = Column(String(50), nullable=False)  # 'math', 'reading', etc.
    diagnostic_completed = Column(Boolean, default=False)
    overall_mastery = Column(DECIMAL(5, 2), default=0.00)
    rank = Column(String(10), default='E')
    boss_defeated = Column(Boolean, default=False)
    total_stars = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserNodeProgress(Base):
    __tablename__ = "user_node_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    node_id = Column(String(100), nullable=False)  # 'math_node_1', 'reading_node_3'
    kingdom_id = Column(String(50), nullable=False)
    mastery_percent = Column(DECIMAL(5, 2), default=0.00)
    stars_earned = Column(Integer, default=0)
    times_completed = Column(Integer, default=0)
    best_accuracy = Column(DECIMAL(5, 2), default=0.00)
    questions_seen = Column(JSONB, default=[])
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

### TAREA 2.3: Crear Migraciones SQL

**Prioridad:** ALTA
**Archivo:** `apps/backend/database/migrations/conquest_mode_tables.sql`

```sql
-- apps/backend/database/migrations/conquest_mode_tables.sql

-- ============================================
-- CONQUEST MODE: Nuevas Tablas
-- Fecha: 29 de Diciembre, 2025
-- ============================================

-- 1. Sistema de Corazones
CREATE TABLE IF NOT EXISTS user_hearts (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_hearts INTEGER NOT NULL DEFAULT 5,
    max_hearts INTEGER NOT NULL DEFAULT 5,
    last_heart_lost_at TIMESTAMP WITH TIME ZONE,
    last_regen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_grace_mode BOOLEAN NOT NULL DEFAULT FALSE,
    ads_watched_today INTEGER NOT NULL DEFAULT 0,
    last_ad_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Sistema de Economia
CREATE TABLE IF NOT EXISTS user_economy (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    gold INTEGER NOT NULL DEFAULT 100,
    total_xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    rank VARCHAR(10) NOT NULL DEFAULT 'E',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    balance_after INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS xp_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    source VARCHAR(50) NOT NULL,
    level_before INTEGER NOT NULL,
    level_after INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Sistema de Rachas
CREATE TABLE IF NOT EXISTS user_streaks (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_activity_date DATE,
    streak_multiplier DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    freeze_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Progreso por Reino
CREATE TABLE IF NOT EXISTS user_kingdom_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kingdom_id VARCHAR(50) NOT NULL,
    diagnostic_completed BOOLEAN DEFAULT FALSE,
    overall_mastery DECIMAL(5,2) DEFAULT 0.00,
    rank VARCHAR(10) DEFAULT 'E',
    boss_defeated BOOLEAN DEFAULT FALSE,
    total_stars INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, kingdom_id)
);

-- 5. Progreso por Nodo
CREATE TABLE IF NOT EXISTS user_node_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    kingdom_id VARCHAR(50) NOT NULL,
    mastery_percent DECIMAL(5,2) DEFAULT 0.00,
    stars_earned INTEGER DEFAULT 0,
    times_completed INTEGER DEFAULT 0,
    best_accuracy DECIMAL(5,2) DEFAULT 0.00,
    questions_seen JSONB DEFAULT '[]'::jsonb,
    is_unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, node_id)
);

-- 6. Tienda
CREATE TABLE IF NOT EXISTS shop_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    cost_gold INTEGER NOT NULL,
    effect JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_inventory (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID REFERENCES shop_items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, item_id)
);

-- 7. Cola de sincronizacion offline
CREATE TABLE IF NOT EXISTS offline_sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    client_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    server_received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_gold_transactions_user ON gold_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_gold_transactions_date ON gold_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_user ON xp_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_node_progress_user ON user_node_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_node_progress_kingdom ON user_node_progress(kingdom_id);
CREATE INDEX IF NOT EXISTS idx_offline_queue_user ON offline_sync_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_offline_queue_processed ON offline_sync_queue(processed);

-- Insertar items iniciales de tienda
INSERT INTO shop_items (name, description, type, cost_gold, effect) VALUES
    ('Streak Freeze', 'Protege tu racha por 1 dia', 'streak_freeze', 200, '{"days": 1}'),
    ('Streak Repair', 'Restaura tu racha perdida', 'streak_repair', 300, '{"restore": true}'),
    ('Heart Refill', 'Recarga todos tus corazones', 'hearts', 150, '{"hearts": 5}'),
    ('Question Hint', 'Elimina 2 opciones incorrectas', 'hint', 50, '{"eliminate": 2}')
ON CONFLICT DO NOTHING;
```

---

## FASE 3: MEDIA (Dias 8-14)

### TAREA 3.1: Crear Endpoint de Sincronizacion Offline

```python
# apps/backend/app/routes/sync.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from typing import List
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/sync", tags=["Sync"])


class OfflineAction(BaseModel):
    action_type: str
    payload: dict
    client_timestamp: datetime


@router.post("/batch")
async def sync_offline_actions(
    actions: List[OfflineAction],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sincroniza acciones realizadas offline"""
    from app.models.economy import OfflineSyncQueue

    results = []

    for action in actions:
        # Guardar en cola
        queue_item = OfflineSyncQueue(
            user_id=uuid.UUID(str(current_user.id)),
            action_type=action.action_type,
            payload=action.payload,
            client_timestamp=action.client_timestamp
        )
        db.add(queue_item)

        # Procesar inmediatamente
        try:
            result = await process_offline_action(db, current_user.id, action)
            queue_item.processed = True
            queue_item.processed_at = datetime.utcnow()
            results.append({"action": action.action_type, "success": True, "result": result})
        except Exception as e:
            queue_item.error_message = str(e)
            results.append({"action": action.action_type, "success": False, "error": str(e)})

    db.commit()
    return {"synced": len(results), "results": results}


async def process_offline_action(db, user_id, action):
    """Procesa una accion offline individual"""
    if action.action_type == "battle_answer":
        # Procesar respuesta de batalla
        from app.services.dungeon_service import dungeon_service
        return dungeon_service.submit_encounter_answer(
            db,
            str(user_id),
            action.payload.get("encounter_id"),
            action.payload.get("question_id"),
            action.payload.get("answer_id"),
            action.payload.get("time_spent_seconds", 30)
        )
    elif action.action_type == "practice_complete":
        # Actualizar rachas
        from app.services.streak_service import streak_service
        return streak_service.check_and_update_streak(
            db,
            str(user_id),
            action.payload.get("xp_earned", 0)
        )

    return {"processed": True}
```

---

### TAREA 3.2: Registrar Rutas en main.py

**Archivo:** `apps/backend/app/main.py`

Agregar los nuevos routers:

```python
# En main.py, agregar imports
from app.routes.hearts import router as hearts_router
from app.routes.economy import router as economy_router
from app.routes.streaks import router as streaks_router
from app.routes.sync import router as sync_router

# En la seccion de include_router
app.include_router(hearts_router, prefix="/api/v1")
app.include_router(economy_router, prefix="/api/v1")
app.include_router(streaks_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
```

---

## CHECKLIST FINAL

### Fase 1: Critica
- [ ] Modificar `dungeon_service.py` para incluir `explanation`
- [ ] Crear modelo `user_hearts`
- [ ] Crear `hearts_service.py`
- [ ] Crear endpoints `/hearts/*`
- [ ] Crear modelo `user_economy`
- [ ] Crear `economy_service.py`
- [ ] Crear endpoints `/economy/*`
- [ ] Ejecutar migraciones SQL

### Fase 2: Alta
- [ ] Crear modelo `user_streaks`
- [ ] Crear `streak_service.py`
- [ ] Crear endpoints `/streaks/*`
- [ ] Crear modelo `user_node_progress`
- [ ] Crear `node_progress_service.py`

### Fase 3: Media
- [ ] Crear endpoint `/sync/batch`
- [ ] Registrar todos los routers en `main.py`
- [ ] Testing de integracion
- [ ] Documentar APIs en Swagger

---

## ENDPOINTS RESUMEN

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/api/v1/hearts/status` | Estado de corazones |
| POST | `/api/v1/hearts/restore-with-ad` | Restaurar con ad |
| POST | `/api/v1/hearts/refill-with-gold` | Recargar con oro |
| POST | `/api/v1/hearts/grace-mode/enter` | Activar modo gracia |
| POST | `/api/v1/hearts/grace-mode/exit` | Desactivar modo gracia |
| GET | `/api/v1/economy/status` | Estado de economia |
| GET | `/api/v1/economy/transactions/gold` | Historial de oro |
| GET | `/api/v1/streaks/status` | Estado de racha |
| POST | `/api/v1/streaks/check` | Verificar racha |
| POST | `/api/v1/streaks/buy-freeze` | Comprar freeze |
| POST | `/api/v1/streaks/repair` | Reparar racha |
| POST | `/api/v1/sync/batch` | Sincronizar offline |

---

> **Documento de Tareas para Claude Code (Backend)**
> Version 1.0 | 29 de Diciembre, 2025
