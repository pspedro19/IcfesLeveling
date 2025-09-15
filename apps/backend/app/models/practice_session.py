from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class PracticeSession(Base):
    """
    Practice session model for "Who Wants to Be a Millionaire" style gameplay
    focused on improving performance on previously failed questions
    """
    __tablename__ = "practice_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session configuration
    session_type = Column(String(50), default="failed_questions_practice")  # failed_questions_practice, adaptive_learning, boss_battle
    target_subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    target_topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    difficulty_level = Column(Integer, default=1)  # 1-10 scale
    
    # Millionaire-style configuration
    max_questions = Column(Integer, default=15)  # Like millionaire's 15 questions
    current_question_index = Column(Integer, default=0)
    lifelines_available = Column(JSON, default={"50_50": True, "ask_ai": True, "skip_question": True})
    
    # Session progress
    status = Column(String(20), default="active")  # active, completed, failed, paused
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    total_experience_gained = Column(Integer, default=0)
    total_orbs_gained = Column(Integer, default=0)
    
    # Performance metrics
    average_response_time = Column(Float, default=0.0)
    difficulty_progression = Column(JSON, default=[])  # Track how difficulty changes
    mastery_improvements = Column(JSON, default={})  # Track specific topic improvements
    
    # Gamification elements
    boss_enemy = Column(String(100), nullable=True)  # Boss name for themed sessions
    current_hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    power_ups_used = Column(JSON, default=[])
    achievements_unlocked = Column(JSON, default=[])
    
    # Session timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_time_seconds = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    #     user = relationship("User", )
    subject = relationship("Subject")
    topic = relationship("Topic")
    #     practice_answers = # relationship("relationship("PracticeAnswer",", cascade="all, delete-orphan")
    #     practice_rewards = # relationship("relationship("PracticeReward",", cascade="all, delete-orphan")

    def calculate_difficulty_boost(self):
        """Calculate dynamic difficulty adjustment based on performance"""
        if self.questions_answered == 0:
            return 0
        
        accuracy = self.correct_answers / self.questions_answered
        streak_bonus = min(self.current_streak * 0.1, 1.0)
        
        # Increase difficulty if doing well, decrease if struggling
        if accuracy >= 0.8 and self.current_streak >= 3:
            return min(2, int(streak_bonus))
        elif accuracy <= 0.5:
            return max(-2, -int((1 - accuracy) * 3))
        return 0

    def get_lifeline_status(self):
        """Get current lifeline availability"""
        return {
            "fifty_fifty": self.lifelines_available.get("50_50", False),
            "ask_ai": self.lifelines_available.get("ask_ai", False),
            "skip_question": self.lifelines_available.get("skip_question", False)
        }

    def use_lifeline(self, lifeline_type: str):
        """Use a lifeline and update availability"""
        if self.lifelines_available.get(lifeline_type, False):
            self.lifelines_available[lifeline_type] = False
            return True
        return False

class PracticeAnswer(Base):
    """
    Individual answers within a practice session, tracking detailed performance
    """
    __tablename__ = "practice_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_session_id = Column(UUID(as_uuid=True), ForeignKey("practice_sessions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    # Answer details
    user_answer = Column(String(10), nullable=True)  # a, b, c, d or null for skipped
    is_correct = Column(Boolean, nullable=True)
    response_time_ms = Column(Integer, default=0)
    
    # Question context
    question_order = Column(Integer, nullable=False)  # Order in the session
    difficulty_at_time = Column(Integer, default=1)
    was_previously_failed = Column(Boolean, default=False)  # If this was a previously failed question
    
    # Lifelines and help used
    lifelines_used = Column(JSON, default=[])  # Which lifelines were used for this question
    fifty_fifty_options = Column(JSON, nullable=True)  # Which options were eliminated
    ai_explanation_requested = Column(Boolean, default=False)
    
    # Performance impact
    experience_gained = Column(Integer, default=0)
    orbs_gained = Column(Integer, default=0)
    damage_dealt = Column(Integer, default=0)  # For boss battle theme
    damage_taken = Column(Integer, default=0)
    
    # Learning analytics
    confidence_level = Column(Integer, default=3)  # 1-5 scale, user-reported confidence
    topic_mastery_before = Column(Float, default=0.0)  # Topic mastery before this question
    topic_mastery_after = Column(Float, default=0.0)   # Topic mastery after this question
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    practice_session = relationship("PracticeSession", )
    question = relationship("Question")
    # ai_explanation = relationship("AIExplanation", uselist=False, cascade="all, delete-orphan")  # Temporarily commented out due to FK issues

class UserQuestionMastery(Base):
    """
    Track individual question mastery and failure patterns for adaptive learning
    """
    __tablename__ = "user_question_mastery"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    # Mastery tracking
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    consecutive_correct = Column(Integer, default=0)
    consecutive_incorrect = Column(Integer, default=0)
    
    # Performance metrics
    average_response_time = Column(Float, default=0.0)
    fastest_correct_time = Column(Integer, nullable=True)
    mastery_level = Column(Float, default=0.0)  # 0.0 to 1.0 scale
    difficulty_comfort = Column(Integer, default=1)  # Difficulty level user is comfortable with
    
    # Learning progression
    first_attempt_date = Column(DateTime(timezone=True))
    last_attempt_date = Column(DateTime(timezone=True))
    mastery_achieved_date = Column(DateTime(timezone=True), nullable=True)  # When they achieved mastery (>85% success)
    needs_review = Column(Boolean, default=True)  # Flag for practice session selection
    
    # Failure analysis
    common_wrong_answers = Column(JSON, default={})  # Track which wrong answers are chosen most
    error_patterns = Column(JSON, default={})  # Categorize types of errors
    improvement_trend = Column(Float, default=0.0)  # Rate of improvement over time
    
    # Contextual factors
    last_failed_in_context = Column(String(50), nullable=True)  # battle, quiz, diagnostic, practice
    topics_confusion = Column(JSON, default=[])  # Related topics causing confusion
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    question = relationship("Question")

    def calculate_mastery_score(self):
        """Calculate current mastery score based on performance"""
        if self.total_attempts == 0:
            return 0.0
        
        accuracy = self.correct_attempts / self.total_attempts
        streak_bonus = min(self.consecutive_correct * 0.1, 0.3)
        recency_bonus = 0.1 if self.consecutive_correct >= 2 else 0.0
        
        base_mastery = accuracy + streak_bonus + recency_bonus
        return min(1.0, max(0.0, base_mastery))

    def update_performance(self, is_correct: bool, response_time_ms: int, user_answer: str):
        """Update mastery metrics after a new attempt"""
        self.total_attempts += 1
        self.last_attempt_date = func.now()
        
        if is_correct:
            self.correct_attempts += 1
            self.consecutive_correct += 1
            self.consecutive_incorrect = 0
            
            if not self.fastest_correct_time or response_time_ms < self.fastest_correct_time:
                self.fastest_correct_time = response_time_ms
        else:
            self.consecutive_incorrect += 1
            self.consecutive_correct = 0
            
            # Track common wrong answers
            if user_answer and user_answer.lower() in ['a', 'b', 'c', 'd']:
                wrong_answers = self.common_wrong_answers or {}
                wrong_answers[user_answer.lower()] = wrong_answers.get(user_answer.lower(), 0) + 1
                self.common_wrong_answers = wrong_answers
        
        # Update average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time_ms / 1000.0
        else:
            self.average_response_time = (self.average_response_time + (response_time_ms / 1000.0)) / 2
        
        # Update mastery level
        self.mastery_level = self.calculate_mastery_score()
        
        # Check if mastery achieved (85% accuracy with at least 3 consecutive correct)
        if (self.mastery_level >= 0.85 and self.consecutive_correct >= 3 and 
            not self.mastery_achieved_date):
            self.mastery_achieved_date = func.now()
            self.needs_review = False
        elif self.consecutive_incorrect >= 2:
            self.needs_review = True

class PracticeReward(Base):
    """
    Rewards earned during practice sessions
    """
    __tablename__ = "practice_rewards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_session_id = Column(UUID(as_uuid=True), ForeignKey("practice_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    reward_type = Column(String(50), nullable=False)  # experience, orbs, item, achievement, rank_up
    reward_data = Column(JSON, nullable=False)  # Specific reward details
    earned_at_question = Column(Integer, nullable=True)  # Which question earned this reward
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    practice_session = relationship("PracticeSession", )
    user = relationship("User")