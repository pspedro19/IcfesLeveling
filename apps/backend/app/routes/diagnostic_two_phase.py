"""
Two-Phase Diagnostic Router
ICFES Leveling Backend

Implements the two-phase diagnostic system as specified in:
- BACKEND_TASKS_CLAUDE.md (Phase 2.1, 2.2)
- API_CONTRACT.md (Section 2: Diagnostic Endpoints)

Endpoints:
- POST /diagnostic/quick/start - Start 15-question quick diagnostic (3 per subject)
- POST /diagnostic/quick/submit - Submit quick diagnostic, calculate theta, assign rank
- POST /diagnostic/deep/start/{subject_id} - Start 15-20 question deep diagnostic per subject
- POST /diagnostic/deep/submit - Submit deep diagnostic, return skill tree
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.question import Question
from ..services.diagnostic_two_phase_service import DiagnosticTwoPhaseService
from ..schemas.diagnostic import (
    DiagnosticQuestion,
    QuestionOption,
    QuickDiagnosticStartResponse,
    QuickDiagnosticSubmitRequest,
    QuickDiagnosticSubmitResponse,
    QuickDiagnosticSubmitResponseIRT,
    DeepDiagnosticStartResponse,
    DeepDiagnosticSubmitRequest,
    DeepDiagnosticSubmitResponse,
    Rank,
    DiagnosticStatusResponse,
    # Adaptive testing schemas
    AdaptiveNextQuestionRequest,
    AdaptiveNextQuestionResponse,
    AdaptiveAnswerRequest,
    AdaptiveAnswerResponse,
    IRTMetrics,
    ThetaProgressionItem,
    SubjectAbility,
)
from ..services.irt_calculation_service import IRTCalculationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostic", tags=["two-phase-diagnostic"])


# =============================================================================
# HELPER FUNCTION (UI Layer)
# =============================================================================

# Define the base path for images. This could also come from a config file.
IMAGE_BASE_URL = "/api/v1/images"

def build_question_response(question: Question, include_topic: bool = False) -> DiagnosticQuestion:
    """
    Build question response schema from Question model, creating full image URLs.
    """
    
    def create_full_url(path: str | None) -> str | None:
        """Helper to construct a full URL from a relative path."""
        if path and path.strip() and path.lower() != 'no aplica':
            # Ensure no leading slashes from the DB path cause issues
            return f"{IMAGE_BASE_URL}/{path.lstrip('/')}"
        return None

    options = []
    for letter in ['A', 'B', 'C', 'D']:
        letter_lower = letter.lower()
        text = getattr(question, f'opcion_{letter_lower}_texto', None) or ""
        relative_image_path = getattr(question, f'opcion_{letter_lower}_imagen', None)

        if not text and question.options and isinstance(question.options, dict):
            text = question.options.get(letter) or question.options.get(letter_lower) or ""

        options.append(QuestionOption(
            id=letter, 
            text=text, 
            image_url=create_full_url(relative_image_path)
        ))

    difficulty_map = {1: "easy", 2: "easy", 3: "medium", 4: "medium", 5: "hard"}
    difficulty_str = difficulty_map.get(question.difficulty, "medium")

    return DiagnosticQuestion(
        id=question.id,
        text=question.pregunta_texto or question.question_text or "Question text not available",
        image_url=create_full_url(question.pregunta_imagen),
        subject_id=question.subject_id,
        subject_name=question.subject.name if question.subject else "Unknown",
        options=options,
        topic_id=question.topic_id if include_topic else None,
        topic_name=question.topic.name if include_topic and question.topic else None,
        difficulty=difficulty_str
    )

# =============================================================================
# QUICK DIAGNOSTIC ENDPOINTS
# =============================================================================

@router.post("/quick/start", response_model=QuickDiagnosticStartResponse)
async def start_quick_diagnostic(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a quick diagnostic test (15 questions - 3 per subject).
    """
    service = DiagnosticTwoPhaseService(db)
    try:
        diagnostic = service.start_quick_diagnostic(current_user.id)
        questions = service.get_quick_diagnostic_questions(diagnostic)
        
        return QuickDiagnosticStartResponse(
            diagnostic_id=diagnostic.id,
            questions=[build_question_response(q) for q in questions],
            total=len(questions),
            time_limit_minutes=10
        )
    except ValueError as e:
        if str(e) == "DIAGNOSTIC_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DIAGNOSTIC_COMPLETED", "message": "Quick diagnostic already completed"}
            )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/quick/submit", response_model=QuickDiagnosticSubmitResponse)
async def submit_quick_diagnostic(
    request: QuickDiagnosticSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit answers for quick diagnostic.
    """
    service = DiagnosticTwoPhaseService(db)
    try:
        result = service.submit_quick_diagnostic(current_user.id, request.diagnostic_id, request.answers)
        return QuickDiagnosticSubmitResponse(
            completed=result["completed"],
            correct=result["correct"],
            total=result["total"],
            rank=Rank(result["rank"]),
            theta=round(result["theta"], 3),
            weak_areas=result["weak_areas"]
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "DIAGNOSTIC_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic not found")
        if error_code == "DIAGNOSTIC_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DIAGNOSTIC_COMPLETED", "message": "This diagnostic has already been submitted"}
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_code)


# =============================================================================
# DEEP DIAGNOSTIC ENDPOINTS
# =============================================================================

@router.post("/deep/start/{subject_id}", response_model=DeepDiagnosticStartResponse)
async def start_deep_diagnostic(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a deep diagnostic test for a specific subject (15-20 questions).
    """
    service = DiagnosticTwoPhaseService(db)
    try:
        diagnostic = service.start_deep_diagnostic(current_user.id, subject_id)
        questions = service.get_deep_diagnostic_questions(diagnostic)
        
        return DeepDiagnosticStartResponse(
            diagnostic_id=diagnostic.id,
            subject_id=diagnostic.subject_id,
            subject_name=diagnostic.subject.name,
            questions=[build_question_response(q, include_topic=True) for q in questions],
            total=len(questions)
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "SUBJECT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        if error_code == "DIAGNOSTIC_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DIAGNOSTIC_COMPLETED", "message": "Deep diagnostic already completed for this subject"}
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_code)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/deep/submit", response_model=DeepDiagnosticSubmitResponse)
async def submit_deep_diagnostic(
    request: DeepDiagnosticSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit answers for deep diagnostic.
    """
    service = DiagnosticTwoPhaseService(db)
    try:
        result = service.submit_deep_diagnostic(current_user.id, request.diagnostic_id, request.answers)
        return DeepDiagnosticSubmitResponse(**result)
    except ValueError as e:
        error_code = str(e)
        if error_code == "DIAGNOSTIC_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic not found")
        if error_code == "DIAGNOSTIC_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DIAGNOSTIC_COMPLETED", "message": "This diagnostic has already been submitted"}
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_code)

# =============================================================================
# ADAPTIVE DIAGNOSTIC ENDPOINTS (IRT-Based)
# =============================================================================

@router.post("/adaptive/next-question", response_model=AdaptiveNextQuestionResponse)
async def get_next_adaptive_question(
    request: AdaptiveNextQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the next optimal question based on current ability estimate using IRT.

    Uses Fisher information function to select the most informative question
    for the examinee's current theta level.
    """
    service = DiagnosticTwoPhaseService(db)
    irt_service = IRTCalculationService(db)

    # Select next question using adaptive algorithm
    question = service.select_next_question_adaptive(
        current_theta=request.current_theta,
        answered_question_ids=request.answered_question_ids,
        subject_id=request.subject_id,
        topic_id=request.topic_id
    )

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suitable questions available for adaptive selection"
        )

    # Calculate information and probability at current theta
    a = question.parametro_irt_a if question.parametro_irt_a is not None else 1.0
    b = question.parametro_irt_b if question.parametro_irt_b is not None else 0.0
    c = question.parametro_irt_c if question.parametro_irt_c is not None else 0.25

    information = irt_service.calculate_information_function(request.current_theta, a, b, c)
    probability = irt_service.calculate_3pl_probability(request.current_theta, a, b, c)

    # Count remaining questions
    from sqlalchemy import and_
    remaining_query = db.query(Question).filter(
        ~Question.id.in_([UUID(qid) for qid in request.answered_question_ids]) if request.answered_question_ids else True
    )
    if request.subject_id:
        remaining_query = remaining_query.filter(Question.subject_id == UUID(request.subject_id))
    remaining_count = remaining_query.count() - 1  # Subtract 1 for the question we're returning

    return AdaptiveNextQuestionResponse(
        question=build_question_response(question),
        information_value=round(information, 4),
        expected_probability=round(probability, 4),
        remaining_questions=max(0, remaining_count)
    )


@router.post("/adaptive/submit-answer", response_model=AdaptiveAnswerResponse)
async def submit_adaptive_answer(
    request: AdaptiveAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an answer and get updated theta estimate using IRT.

    Returns the new theta estimate, standard error, and selection for next question.
    """
    service = DiagnosticTwoPhaseService(db)
    irt_service = IRTCalculationService(db)

    # Get the question
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Check if answer is correct
    is_correct = request.answer_id.upper() == (question.respuesta_correcta or "").upper()
    correct_answer = question.respuesta_correcta.upper() if question.respuesta_correcta else "A"

    # Update theta using IRT adaptive method
    new_theta, new_se = irt_service.update_theta_adaptive(
        current_theta=request.current_theta,
        current_se=request.current_se,
        new_response=is_correct,
        question=question
    )

    # Calculate theta change
    theta_change = new_theta - request.current_theta

    # Calculate percentile
    percentile = service.theta_to_percentile(new_theta)

    # Determine rank
    from ..services.diagnostic_two_phase_service import _theta_to_rank
    rank = _theta_to_rank(new_theta)

    # Calculate confidence interval
    ci_lower = new_theta - 1.96 * new_se
    ci_upper = new_theta + 1.96 * new_se

    return AdaptiveAnswerResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        new_theta=round(new_theta, 4),
        new_se=round(new_se, 4),
        theta_change=round(theta_change, 4),
        percentile=percentile,
        rank=Rank(rank),
        confidence_interval_95=[round(ci_lower, 4), round(ci_upper, 4)]
    )


@router.post("/adaptive/batch-questions")
async def get_adaptive_question_batch(
    current_theta: float,
    subject_id: str,
    answered_question_ids: List[str] = [],
    batch_size: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a batch of questions sorted by information value at current theta.

    Useful for prefetching questions in adaptive testing scenarios.
    """
    service = DiagnosticTwoPhaseService(db)

    questions = service.get_adaptive_questions_batch(
        current_theta=current_theta,
        answered_question_ids=answered_question_ids,
        subject_id=subject_id,
        batch_size=batch_size
    )

    return {
        "questions": [build_question_response(q) for q in questions],
        "count": len(questions),
        "current_theta": current_theta
    }


@router.post("/quick/submit-irt", response_model=QuickDiagnosticSubmitResponseIRT)
async def submit_quick_diagnostic_with_irt(
    request: QuickDiagnosticSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit answers for quick diagnostic with full IRT analysis.

    Returns comprehensive IRT metrics including:
    - MLE theta estimate with standard error
    - 95% confidence interval
    - Theta progression over the test
    - Subject-specific ability estimates
    - Percentile rank
    """
    service = DiagnosticTwoPhaseService(db)
    try:
        result = service.submit_quick_diagnostic_irt(
            current_user.id,
            request.diagnostic_id,
            request.answers
        )

        # Transform subject_abilities dict to use SubjectAbility schema
        subject_abilities = {}
        if "irt_metrics" in result and "subject_abilities" in result["irt_metrics"]:
            for subject_id, ability_data in result["irt_metrics"]["subject_abilities"].items():
                subject_abilities[subject_id] = SubjectAbility(**ability_data)

        # Transform theta_progression to use ThetaProgressionItem schema
        theta_progression = []
        if "irt_metrics" in result and "theta_progression" in result["irt_metrics"]:
            for item in result["irt_metrics"]["theta_progression"]:
                theta_progression.append(ThetaProgressionItem(**item))

        return QuickDiagnosticSubmitResponseIRT(
            completed=result["completed"],
            correct=result["correct"],
            total=result["total"],
            rank=Rank(result["rank"]),
            theta=result["theta"],
            weak_areas=result["weak_areas"],
            irt_metrics=IRTMetrics(
                theta_estimate=result["irt_metrics"]["theta_estimate"],
                standard_error=result["irt_metrics"]["standard_error"],
                confidence_interval_95=result["irt_metrics"]["confidence_interval_95"],
                percentile=result["irt_metrics"]["percentile"],
                theta_progression=theta_progression,
                subject_abilities=subject_abilities
            )
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "DIAGNOSTIC_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnostic not found"
            )
        if error_code == "DIAGNOSTIC_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DIAGNOSTIC_COMPLETED", "message": "This diagnostic has already been submitted"}
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_code)


@router.get("/irt/calculate-theta")
async def calculate_theta_from_responses(
    diagnostic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate theta from stored diagnostic responses using IRT 3PL model.

    Useful for recalculating theta after a diagnostic is complete.
    """
    from ..models.diagnostic_two_phase import TwoPhaseDignostic, TwoPhaseDiagnosticAnswer

    # Get diagnostic and answers
    diagnostic = db.query(TwoPhaseDignostic).filter(
        TwoPhaseDignostic.id == diagnostic_id,
        TwoPhaseDignostic.user_id == current_user.id
    ).first()

    if not diagnostic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic not found"
        )

    # Get answers
    answers = db.query(TwoPhaseDiagnosticAnswer).filter(
        TwoPhaseDiagnosticAnswer.diagnostic_id == diagnostic_id
    ).all()

    if not answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No answers found for this diagnostic"
        )

    service = DiagnosticTwoPhaseService(db)

    # Build responses list
    responses = []
    for answer in answers:
        responses.append({
            'question_id': answer.question_id,
            'is_correct': answer.was_correct
        })

    # Calculate theta with progression
    result = service.calculate_theta_with_progression(responses)

    # Calculate subject thetas
    subject_thetas = service.calculate_subject_thetas(responses)

    return {
        "diagnostic_id": str(diagnostic_id),
        "theta_final": result["theta_final"],
        "standard_error": result["standard_error"],
        "confidence_interval_95": result["confidence_interval"],
        "percentile": service.theta_to_percentile(result["theta_final"]),
        "rank": _theta_to_rank(result["theta_final"]),
        "theta_progression": result["progression"],
        "subject_abilities": subject_thetas
    }


# Import for the function
from ..services.diagnostic_two_phase_service import _theta_to_rank