from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.practice_service import PracticeService
from ..schemas.practice import (
    PracticeConfigRequest,
    PracticeSessionResponse,
    AnswerSubmitRequest,
    AnswerResultResponse,
    LifelineResultResponse,
    SessionResultsResponse
)

router = APIRouter(prefix="/practice", tags=["Practice - Millonario"])


@router.post("/start", response_model=PracticeSessionResponse)
async def start_practice_session(
    config: PracticeConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Iniciar nueva sesión de práctica estilo Millonario.

    - session_type: "practice", "failed_questions", "boss_battle"
    - subject_id: Filtrar por materia (opcional)
    - topic_id: Filtrar por tema (opcional)
    - difficulty: 1-10 (opcional, default 5)
    - max_questions: Número de preguntas (default 15)
    """
    try:
        service = PracticeService(db)
        session = service.create_session(
            user_id=current_user.id,
            session_type=config.session_type,
            subject_id=config.subject_id,
            topic_id=config.topic_id,
            difficulty=config.difficulty,
            max_questions=config.max_questions
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating practice session")


@router.get("/history/me", response_model=List[PracticeSessionResponse])
async def get_my_practice_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener historial de sesiones de práctica"""
    try:
        service = PracticeService(db)
        return service.get_user_history(current_user.id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching practice history")


@router.get("/{session_id}", response_model=PracticeSessionResponse)
async def get_session_status(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estado actual de la sesión"""
    try:
        service = PracticeService(db)
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching session")


@router.get("/{session_id}/question")
async def get_current_question(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener la pregunta actual"""
    try:
        service = PracticeService(db)
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        question = service.get_current_question(session_id)
        if not question:
            raise HTTPException(status_code=404, detail="No question available")
        return question
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching question")


@router.post("/{session_id}/answer", response_model=AnswerResultResponse)
async def submit_answer(
    session_id: UUID,
    answer: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enviar respuesta a la pregunta actual.

    - question_id: UUID de la pregunta
    - selected_answer: "A", "B", "C", o "D"
    - response_time_ms: Tiempo de respuesta en milisegundos
    """
    try:
        service = PracticeService(db)
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return service.submit_answer(
            session_id=session_id,
            question_id=answer.question_id,
            answer=answer.selected_answer,
            response_time_ms=answer.response_time_ms
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error submitting answer")


@router.post("/{session_id}/lifeline/fifty-fifty", response_model=LifelineResultResponse)
async def use_fifty_fifty(
    session_id: UUID,
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Usar comodín 50/50.

    Elimina 2 opciones incorrectas.
    Solo se puede usar 1 vez por sesión.
    """
    try:
        service = PracticeService(db)
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        eliminated = service.use_fifty_fifty(session_id, question_id)
        return {"lifeline_type": "fifty_fifty", "eliminated_options": eliminated, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error using 50/50 lifeline")


@router.post("/{session_id}/lifeline/ask-ai", response_model=LifelineResultResponse)
async def use_ask_ai(
    session_id: UUID,
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Usar comodín "Preguntar a la IA".

    Recibe una pista (no la respuesta) generada por IA.
    Solo se puede usar 1 vez por sesión.
    """
    try:
        service = PracticeService(db)
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        hint = service.use_ask_ai(session_id, question_id)
        return {"lifeline_type": "ask_ai", "hint": hint, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error using Ask AI lifeline")


@router.post("/{session_id}/lifeline/skip", response_model=LifelineResultResponse)
async def use_skip(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Saltar la pregunta actual.

    No suma ni resta puntos.
    Solo se puede usar 1 vez por sesión.
    """
    try:
        service = PracticeService(db)
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        result = service.use_skip(session_id)
        return {"lifeline_type": "skip", "success": result.get("success", True)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error using skip lifeline")


@router.post("/{session_id}/complete", response_model=SessionResultsResponse)
async def complete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finalizar sesión y obtener resultados.

    Calcula estadísticas, otorga recompensas y actualiza logros.
    """
    try:
        service = PracticeService(db)
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return service.complete_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error completing session")
