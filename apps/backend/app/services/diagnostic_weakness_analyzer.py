"""
Diagnostic Weakness Analysis Engine
Advanced analysis of student diagnostic test results to identify specific learning gaps
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

@dataclass
class WeaknessPattern:
    """Represents a specific weakness pattern identified in the diagnostic"""
    topic_id: str
    topic_name: str
    failed_questions: List[str]
    difficulty_range: Tuple[float, float]
    error_types: List[str]
    severity_score: float
    frequency: int
    avg_response_time: float
    confidence_level: str
    remediation_priority: int
    specific_concepts: List[str]
    suggested_focus_areas: List[str]

@dataclass
class StrengthPattern:
    """Represents areas where student performed well"""
    topic_id: str
    topic_name: str
    correct_questions: List[str]
    difficulty_range: Tuple[float, float]
    mastery_score: float
    consistency_score: float
    avg_response_time: float
    advanced_ready: bool

@dataclass
class LearningGap:
    """Represents a specific learning gap requiring attention"""
    gap_id: str
    title: str
    description: str
    prerequisite_concepts: List[str]
    target_concepts: List[str]
    estimated_difficulty: int
    time_investment: float
    learning_objectives: List[str]
    success_criteria: List[str]

class DiagnosticWeaknessAnalyzer:
    """
    Advanced analyzer for extracting actionable insights from diagnostic test results
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Define error patterns and their indicators
        self.error_patterns = {
            'conceptual_misunderstanding': ['wrong_formula', 'wrong_principle'],
            'procedural_error': ['calculation_error', 'step_missing'],
            'reading_comprehension': ['misread_question', 'missed_key_info'],
            'time_management': ['rushed_answer', 'incomplete_solution'],
            'careless_mistake': ['arithmetic_error', 'sign_error'],
            'knowledge_gap': ['unknown_concept', 'unfamiliar_context']
        }
    
    async def analyze_diagnostic_results(
        self,
        user_id: str,
        subject_id: str,
        diagnostic_test_id: str
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of diagnostic test results
        """
        try:
            logger.info(f"🔍 Analyzing diagnostic results for user {user_id}, test {diagnostic_test_id}")
            
            # 1. Get detailed test data
            test_data = await self._get_detailed_test_data(diagnostic_test_id, user_id, subject_id)
            if not test_data['success']:
                return test_data
            
            # 2. Analyze answer patterns
            answer_analysis = await self._analyze_answer_patterns(test_data['answers'])
            
            # 3. Identify weakness patterns
            weakness_patterns = await self._identify_weakness_patterns(
                test_data['answers'], test_data['questions_metadata']
            )
            
            # 4. Identify strength patterns
            strength_patterns = await self._identify_strength_patterns(
                test_data['answers'], test_data['questions_metadata']
            )
            
            # 5. Map to specific learning gaps
            learning_gaps = await self._map_to_learning_gaps(
                weakness_patterns, subject_id
            )
            
            # 6. Generate remediation recommendations
            remediation_plan = await self._generate_remediation_plan(
                weakness_patterns, learning_gaps, strength_patterns
            )
            
            # 7. Calculate learning trajectory
            learning_trajectory = await self._calculate_learning_trajectory(
                weakness_patterns, strength_patterns, test_data['overall_score']
            )
            
            analysis_result = {
                'success': True,
                'user_id': user_id,
                'subject_id': subject_id,
                'diagnostic_test_id': diagnostic_test_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'overall_metrics': {
                    'total_questions': len(test_data['answers']),
                    'correct_answers': sum(1 for a in test_data['answers'] if a['is_correct']),
                    'accuracy_rate': test_data['overall_score'] / 100,
                    'avg_response_time': test_data['avg_response_time'],
                    'difficulty_spread': test_data['difficulty_spread']
                },
                'answer_patterns': answer_analysis,
                'weakness_patterns': [asdict(wp) for wp in weakness_patterns],
                'strength_patterns': [asdict(sp) for sp in strength_patterns],
                'learning_gaps': [asdict(lg) for lg in learning_gaps],
                'remediation_plan': remediation_plan,
                'learning_trajectory': learning_trajectory,
                'priority_areas': self._get_priority_areas(weakness_patterns),
                'next_steps': self._generate_next_steps(learning_gaps, remediation_plan)
            }
            
            # 8. Save analysis to database
            await self._save_analysis_results(diagnostic_test_id, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing diagnostic results: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to analyze diagnostic results'
            }
    
    async def _get_detailed_test_data(
        self,
        diagnostic_test_id: str,
        user_id: str,
        subject_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive test data including questions metadata"""
        try:
            query = text("""
                SELECT 
                    dt.score_percentage,
                    dt.time_spent_seconds,
                    json_agg(
                        json_build_object(
                            'answer_id', dta.id,
                            'question_id', dta.question_id,
                            'user_answer', dta.user_answer,
                            'is_correct', dta.is_correct,
                            'response_time_ms', dta.response_time_ms,
                            'hints_used', dta.hints_used,
                            'topic_id', dta.topic_id,
                            'question_text', q.question_text,
                            'correct_answer', q.correct_answer,
                            'difficulty_theta', q.difficulty_theta,
                            'question_type', q.question_type,
                            'cognitive_level', q.cognitive_level,
                            'topic_name', t.name,
                            'subject_name', s.name,
                            'competency', q.competency,
                            'component', q.component,
                            'distractors', q.options
                        )
                    ) as answers_data
                FROM diagnostic_tests dt
                LEFT JOIN diagnostic_test_answers dta ON dt.id = dta.diagnostic_test_id
                LEFT JOIN questions q ON dta.question_id = q.id
                LEFT JOIN topics t ON dta.topic_id = t.id
                LEFT JOIN subjects s ON dt.subject_id = s.id
                WHERE dt.id = :diagnostic_test_id 
                AND dt.user_id = :user_id 
                AND dt.subject_id = :subject_id
                GROUP BY dt.id, dt.score_percentage, dt.time_spent_seconds
            """)
            
            result = self.db.execute(query, {
                'diagnostic_test_id': diagnostic_test_id,
                'user_id': user_id,
                'subject_id': subject_id
            }).first()
            
            if not result:
                return {'success': False, 'error': 'Diagnostic test not found'}
            
            answers = json.loads(result[2]) if result[2] else []
            
            # Calculate additional metrics
            response_times = [a['response_time_ms'] for a in answers if a['response_time_ms']]
            difficulties = [a['difficulty_theta'] for a in answers if a['difficulty_theta']]
            
            questions_metadata = {}
            for answer in answers:
                questions_metadata[answer['question_id']] = {
                    'difficulty': answer['difficulty_theta'],
                    'cognitive_level': answer['cognitive_level'],
                    'competency': answer['competency'],
                    'component': answer['component'],
                    'topic': answer['topic_name']
                }
            
            return {
                'success': True,
                'overall_score': result[0],
                'total_time_seconds': result[1],
                'answers': answers,
                'questions_metadata': questions_metadata,
                'avg_response_time': np.mean(response_times) if response_times else 0,
                'difficulty_spread': {
                    'min': min(difficulties) if difficulties else 0,
                    'max': max(difficulties) if difficulties else 0,
                    'mean': np.mean(difficulties) if difficulties else 0,
                    'std': np.std(difficulties) if difficulties else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed test data: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _analyze_answer_patterns(self, answers: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in student answers"""
        patterns = {
            'response_time_analysis': {},
            'difficulty_performance': {},
            'cognitive_level_performance': {},
            'error_distribution': {},
            'hint_usage_patterns': {}
        }
        
        # Response time analysis
        correct_times = [a['response_time_ms'] for a in answers if a['is_correct'] and a['response_time_ms']]
        incorrect_times = [a['response_time_ms'] for a in answers if not a['is_correct'] and a['response_time_ms']]
        
        patterns['response_time_analysis'] = {
            'avg_correct_time': np.mean(correct_times) if correct_times else 0,
            'avg_incorrect_time': np.mean(incorrect_times) if incorrect_times else 0,
            'time_efficiency': np.mean(correct_times) / np.mean(incorrect_times) if correct_times and incorrect_times else 1,
            'rushed_answers': len([t for t in incorrect_times if t < 30000])  # Less than 30 seconds
        }
        
        # Difficulty performance
        difficulty_groups = defaultdict(list)
        for answer in answers:
            if answer['difficulty_theta'] is not None:
                difficulty_level = self._categorize_difficulty(answer['difficulty_theta'])
                difficulty_groups[difficulty_level].append(answer['is_correct'])
        
        for level, results in difficulty_groups.items():
            patterns['difficulty_performance'][level] = {
                'accuracy': sum(results) / len(results),
                'total_questions': len(results)
            }
        
        # Cognitive level performance
        cognitive_groups = defaultdict(list)
        for answer in answers:
            if answer['cognitive_level']:
                cognitive_groups[answer['cognitive_level']].append(answer['is_correct'])
        
        for level, results in cognitive_groups.items():
            patterns['cognitive_level_performance'][level] = {
                'accuracy': sum(results) / len(results),
                'total_questions': len(results)
            }
        
        # Error distribution by topic
        incorrect_by_topic = defaultdict(int)
        total_by_topic = defaultdict(int)
        
        for answer in answers:
            topic = answer['topic_name']
            total_by_topic[topic] += 1
            if not answer['is_correct']:
                incorrect_by_topic[topic] += 1
        
        for topic in total_by_topic:
            patterns['error_distribution'][topic] = {
                'error_rate': incorrect_by_topic[topic] / total_by_topic[topic],
                'error_count': incorrect_by_topic[topic],
                'total_questions': total_by_topic[topic]
            }
        
        # Hint usage patterns
        hint_usage = [a['hints_used'] for a in answers if a['hints_used'] is not None]
        patterns['hint_usage_patterns'] = {
            'avg_hints_per_question': np.mean(hint_usage) if hint_usage else 0,
            'questions_with_hints': len([h for h in hint_usage if h > 0]),
            'total_hints_used': sum(hint_usage),
            'hint_effectiveness': self._calculate_hint_effectiveness(answers)
        }
        
        return patterns
    
    def _categorize_difficulty(self, theta: float) -> str:
        """Categorize difficulty based on theta value"""
        if theta < -1:
            return 'easy'
        elif theta < 0:
            return 'medium'
        elif theta < 1:
            return 'hard'
        else:
            return 'very_hard'
    
    def _calculate_hint_effectiveness(self, answers: List[Dict]) -> float:
        """Calculate how effective hints were in helping students"""
        hint_questions = [a for a in answers if a['hints_used'] and a['hints_used'] > 0]
        if not hint_questions:
            return 0.0
        
        correct_with_hints = sum(1 for a in hint_questions if a['is_correct'])
        return correct_with_hints / len(hint_questions)
    
    async def _identify_weakness_patterns(
        self,
        answers: List[Dict],
        questions_metadata: Dict[str, Dict]
    ) -> List[WeaknessPattern]:
        """Identify specific weakness patterns from incorrect answers"""
        patterns = []
        
        # Group incorrect answers by topic
        incorrect_by_topic = defaultdict(list)
        for answer in answers:
            if not answer['is_correct']:
                topic_id = answer['topic_id']
                topic_name = answer['topic_name']
                incorrect_by_topic[(topic_id, topic_name)].append(answer)
        
        for (topic_id, topic_name), incorrect_answers in incorrect_by_topic.items():
            if len(incorrect_answers) >= 1:  # At least 1 incorrect answer to form a pattern
                
                # Calculate metrics
                difficulties = [a['difficulty_theta'] for a in incorrect_answers if a['difficulty_theta']]
                response_times = [a['response_time_ms'] for a in incorrect_answers if a['response_time_ms']]
                
                # Analyze error types
                error_types = await self._analyze_error_types(incorrect_answers)
                
                # Calculate severity score
                severity_score = self._calculate_severity_score(
                    len(incorrect_answers),
                    difficulties,
                    len(answers)
                )
                
                # Determine specific concepts that need work
                specific_concepts = await self._extract_specific_concepts(
                    incorrect_answers, topic_name
                )
                
                # Generate suggested focus areas
                focus_areas = await self._generate_focus_areas(
                    incorrect_answers, error_types, topic_name
                )
                
                pattern = WeaknessPattern(
                    topic_id=topic_id,
                    topic_name=topic_name,
                    failed_questions=[a['question_id'] for a in incorrect_answers],
                    difficulty_range=(min(difficulties) if difficulties else 0, 
                                    max(difficulties) if difficulties else 0),
                    error_types=error_types,
                    severity_score=severity_score,
                    frequency=len(incorrect_answers),
                    avg_response_time=np.mean(response_times) if response_times else 0,
                    confidence_level=self._determine_confidence_level(severity_score),
                    remediation_priority=self._calculate_remediation_priority(
                        severity_score, len(incorrect_answers), difficulties
                    ),
                    specific_concepts=specific_concepts,
                    suggested_focus_areas=focus_areas
                )
                
                patterns.append(pattern)
        
        # Sort by remediation priority
        patterns.sort(key=lambda x: x.remediation_priority, reverse=True)
        
        return patterns
    
    async def _identify_strength_patterns(
        self,
        answers: List[Dict],
        questions_metadata: Dict[str, Dict]
    ) -> List[StrengthPattern]:
        """Identify areas where student performed well"""
        patterns = []
        
        # Group correct answers by topic
        correct_by_topic = defaultdict(list)
        for answer in answers:
            if answer['is_correct']:
                topic_id = answer['topic_id']
                topic_name = answer['topic_name']
                correct_by_topic[(topic_id, topic_name)].append(answer)
        
        for (topic_id, topic_name), correct_answers in correct_by_topic.items():
            if len(correct_answers) >= 2:  # At least 2 correct answers to show strength
                
                difficulties = [a['difficulty_theta'] for a in correct_answers if a['difficulty_theta']]
                response_times = [a['response_time_ms'] for a in correct_answers if a['response_time_ms']]
                
                # Calculate mastery score
                mastery_score = self._calculate_mastery_score(
                    len(correct_answers), difficulties
                )
                
                # Calculate consistency
                consistency_score = self._calculate_consistency_score(
                    correct_answers, topic_id, answers
                )
                
                pattern = StrengthPattern(
                    topic_id=topic_id,
                    topic_name=topic_name,
                    correct_questions=[a['question_id'] for a in correct_answers],
                    difficulty_range=(min(difficulties) if difficulties else 0,
                                    max(difficulties) if difficulties else 0),
                    mastery_score=mastery_score,
                    consistency_score=consistency_score,
                    avg_response_time=np.mean(response_times) if response_times else 0,
                    advanced_ready=mastery_score > 0.8 and consistency_score > 0.7
                )
                
                patterns.append(pattern)
        
        # Sort by mastery score
        patterns.sort(key=lambda x: x.mastery_score, reverse=True)
        
        return patterns
    
    async def _analyze_error_types(self, incorrect_answers: List[Dict]) -> List[str]:
        """Analyze types of errors made in incorrect answers"""
        error_types = []
        
        for answer in incorrect_answers:
            # Analyze based on response time
            if answer['response_time_ms'] and answer['response_time_ms'] < 30000:
                error_types.append('rushed_answer')
            elif answer['response_time_ms'] and answer['response_time_ms'] > 300000:
                error_types.append('overthinking')
            
            # Analyze based on hint usage
            if answer['hints_used'] and answer['hints_used'] > 2:
                error_types.append('knowledge_gap')
            elif answer['hints_used'] and answer['hints_used'] == 0:
                error_types.append('overconfidence')
            
            # Analyze based on difficulty
            if answer['difficulty_theta'] and answer['difficulty_theta'] < -1:
                error_types.append('careless_mistake')
            elif answer['difficulty_theta'] and answer['difficulty_theta'] > 1:
                error_types.append('advanced_concept_gap')
        
        # Return unique error types
        return list(set(error_types))
    
    async def _extract_specific_concepts(
        self,
        incorrect_answers: List[Dict],
        topic_name: str
    ) -> List[str]:
        """Extract specific concepts that need attention within a topic"""
        # This would ideally use NLP to analyze question content
        # For now, return general concepts based on topic
        concept_map = {
            'Algebra': ['Linear equations', 'Quadratic functions', 'Polynomial operations', 'Factoring'],
            'Geometry': ['Area and perimeter', 'Volume calculations', 'Angle relationships', 'Coordinate geometry'],
            'Trigonometry': ['Basic ratios', 'Unit circle', 'Identities', 'Applications'],
            'Statistics': ['Data interpretation', 'Probability calculations', 'Distributions', 'Hypothesis testing'],
            'Reading Comprehension': ['Main idea identification', 'Inference skills', 'Context clues', 'Text structure'],
            'Grammar': ['Verb tenses', 'Subject-verb agreement', 'Punctuation', 'Sentence structure'],
            'Chemistry': ['Chemical bonding', 'Stoichiometry', 'Periodic trends', 'Reaction mechanisms'],
            'Physics': ['Motion equations', 'Force and energy', 'Wave properties', 'Thermodynamics'],
            'Biology': ['Cell structure', 'Genetics', 'Evolution', 'Ecology']
        }
        
        base_concepts = concept_map.get(topic_name, [f'Basic {topic_name} concepts'])
        
        # Select concepts based on number of errors
        num_concepts = min(len(incorrect_answers), len(base_concepts))
        return base_concepts[:num_concepts]
    
    async def _generate_focus_areas(
        self,
        incorrect_answers: List[Dict],
        error_types: List[str],
        topic_name: str
    ) -> List[str]:
        """Generate specific focus areas for remediation"""
        focus_areas = []
        
        # Based on error types
        if 'rushed_answer' in error_types:
            focus_areas.append('Slow down and read questions carefully')
        if 'knowledge_gap' in error_types:
            focus_areas.append(f'Review fundamental {topic_name} concepts')
        if 'careless_mistake' in error_types:
            focus_areas.append('Practice attention to detail and checking work')
        if 'advanced_concept_gap' in error_types:
            focus_areas.append(f'Build up to advanced {topic_name} topics gradually')
        
        # Based on frequency
        if len(incorrect_answers) > 3:
            focus_areas.append(f'Intensive {topic_name} practice needed')
        
        # Default focus areas
        if not focus_areas:
            focus_areas = [
                f'Practice {topic_name} problems',
                f'Review {topic_name} theory',
                f'Work through {topic_name} examples'
            ]
        
        return focus_areas[:3]  # Limit to top 3
    
    def _calculate_severity_score(
        self,
        error_count: int,
        difficulties: List[float],
        total_questions: int
    ) -> float:
        """Calculate severity score for a weakness pattern"""
        if total_questions == 0:
            return 0.0
        
        # Base severity on error frequency
        frequency_score = error_count / total_questions
        
        # Adjust for difficulty - easier questions failed = higher severity
        if difficulties:
            avg_difficulty = np.mean(difficulties)
            difficulty_factor = max(0.5, 1.0 - avg_difficulty)  # Easier = higher factor
        else:
            difficulty_factor = 1.0
        
        severity = frequency_score * difficulty_factor
        return min(1.0, severity)
    
    def _determine_confidence_level(self, severity_score: float) -> str:
        """Determine confidence level based on severity score"""
        if severity_score >= 0.7:
            return 'high'
        elif severity_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_remediation_priority(
        self,
        severity_score: float,
        error_count: int,
        difficulties: List[float]
    ) -> int:
        """Calculate priority for remediation (1-10, 10 being highest priority)"""
        base_priority = severity_score * 5  # 0-5 range
        
        # Boost for frequency
        frequency_boost = min(2, error_count * 0.5)
        
        # Boost for easy questions failed
        if difficulties:
            easy_questions_failed = sum(1 for d in difficulties if d < -0.5)
            easy_boost = easy_questions_failed * 0.5
        else:
            easy_boost = 0
        
        total_priority = base_priority + frequency_boost + easy_boost
        return min(10, max(1, int(total_priority)))
    
    def _calculate_mastery_score(self, correct_count: int, difficulties: List[float]) -> float:
        """Calculate mastery score for a strength pattern"""
        if not difficulties:
            return 0.5
        
        # Base score on correct count
        base_score = min(1.0, correct_count * 0.2)
        
        # Boost for harder questions
        avg_difficulty = np.mean(difficulties)
        difficulty_boost = max(0, avg_difficulty * 0.3)
        
        return min(1.0, base_score + difficulty_boost)
    
    def _calculate_consistency_score(
        self,
        correct_answers: List[Dict],
        topic_id: str,
        all_answers: List[Dict]
    ) -> float:
        """Calculate consistency score within a topic"""
        topic_answers = [a for a in all_answers if a['topic_id'] == topic_id]
        if not topic_answers:
            return 0.0
        
        correct_count = len(correct_answers)
        total_count = len(topic_answers)
        
        return correct_count / total_count
    
    async def _map_to_learning_gaps(
        self,
        weakness_patterns: List[WeaknessPattern],
        subject_id: str
    ) -> List[LearningGap]:
        """Map weakness patterns to specific learning gaps"""
        gaps = []
        
        for i, pattern in enumerate(weakness_patterns):
            gap_id = f"gap_{i+1}_{pattern.topic_id}"
            
            # Determine prerequisites based on topic
            prerequisites = await self._get_prerequisite_concepts(pattern.topic_name, subject_id)
            
            gap = LearningGap(
                gap_id=gap_id,
                title=f"Learning Gap in {pattern.topic_name}",
                description=f"Student struggles with {pattern.topic_name} concepts, "
                           f"showing {pattern.frequency} incorrect responses with "
                           f"{pattern.confidence_level} confidence level.",
                prerequisite_concepts=prerequisites,
                target_concepts=pattern.specific_concepts,
                estimated_difficulty=min(5, pattern.remediation_priority // 2),
                time_investment=self._estimate_time_investment(pattern),
                learning_objectives=self._generate_learning_objectives_for_gap(pattern),
                success_criteria=self._generate_success_criteria(pattern)
            )
            
            gaps.append(gap)
        
        return gaps
    
    async def _get_prerequisite_concepts(self, topic_name: str, subject_id: str) -> List[str]:
        """Get prerequisite concepts for a topic"""
        # This would ideally query a curriculum database
        # For now, return general prerequisites
        prerequisite_map = {
            'Quadratic Functions': ['Linear equations', 'Basic algebra', 'Graphing'],
            'Trigonometry': ['Geometry basics', 'Angle measurement', 'Right triangles'],
            'Statistics': ['Basic arithmetic', 'Fractions', 'Percentages'],
            'Reading Comprehension': ['Vocabulary building', 'Basic grammar'],
            'Chemical Bonding': ['Atomic structure', 'Periodic table', 'Electron configuration']
        }
        
        return prerequisite_map.get(topic_name, ['Basic concepts'])
    
    def _estimate_time_investment(self, pattern: WeaknessPattern) -> float:
        """Estimate time investment needed to address weakness"""
        base_time = 2.0  # Base 2 hours
        
        # Adjust for severity
        severity_multiplier = 1 + pattern.severity_score
        
        # Adjust for frequency
        frequency_multiplier = 1 + (pattern.frequency * 0.2)
        
        total_time = base_time * severity_multiplier * frequency_multiplier
        return min(20.0, total_time)  # Cap at 20 hours
    
    def _generate_learning_objectives_for_gap(self, pattern: WeaknessPattern) -> List[str]:
        """Generate specific learning objectives for a learning gap"""
        objectives = [
            f"Understand core concepts in {pattern.topic_name}",
            f"Solve {pattern.topic_name} problems with 80% accuracy",
            f"Apply {pattern.topic_name} concepts to new situations"
        ]
        
        # Add specific objectives based on error types
        if 'rushed_answer' in pattern.error_types:
            objectives.append("Develop systematic problem-solving approach")
        if 'knowledge_gap' in pattern.error_types:
            objectives.append("Master fundamental vocabulary and definitions")
        
        return objectives
    
    def _generate_success_criteria(self, pattern: WeaknessPattern) -> List[str]:
        """Generate success criteria for addressing the weakness"""
        return [
            f"Score 80% or higher on {pattern.topic_name} practice questions",
            f"Complete practice set without hints in {pattern.topic_name}",
            f"Explain {pattern.topic_name} concepts clearly to others",
            "Demonstrate consistent performance across different question types"
        ]
    
    async def _generate_remediation_plan(
        self,
        weakness_patterns: List[WeaknessPattern],
        learning_gaps: List[LearningGap],
        strength_patterns: List[StrengthPattern]
    ) -> Dict[str, Any]:
        """Generate comprehensive remediation plan"""
        plan = {
            'phase_1_foundation': {
                'duration_weeks': 2,
                'focus_areas': [],
                'activities': [],
                'success_metrics': []
            },
            'phase_2_skill_building': {
                'duration_weeks': 4,
                'focus_areas': [],
                'activities': [],
                'success_metrics': []
            },
            'phase_3_mastery': {
                'duration_weeks': 2,
                'focus_areas': [],
                'activities': [],
                'success_metrics': []
            },
            'leveraged_strengths': [sp.topic_name for sp in strength_patterns if sp.advanced_ready],
            'total_estimated_weeks': 8
        }
        
        # Sort gaps by priority
        high_priority_gaps = [gap for gap in learning_gaps 
                            if any(wp.remediation_priority >= 7 
                                 for wp in weakness_patterns 
                                 if wp.topic_name in gap.title)]
        
        # Phase 1: Foundation
        plan['phase_1_foundation']['focus_areas'] = [gap.title for gap in high_priority_gaps[:2]]
        plan['phase_1_foundation']['activities'] = [
            'Review prerequisite concepts',
            'Complete guided practice exercises',
            'Watch explanatory videos'
        ]
        
        # Phase 2: Skill Building
        plan['phase_2_skill_building']['focus_areas'] = [gap.title for gap in learning_gaps[2:5]]
        plan['phase_2_skill_building']['activities'] = [
            'Solve practice problems',
            'Apply concepts to new contexts',
            'Take mini-assessments'
        ]
        
        # Phase 3: Mastery
        plan['phase_3_mastery']['focus_areas'] = ['Integration and application']
        plan['phase_3_mastery']['activities'] = [
            'Complete comprehensive practice tests',
            'Solve complex, multi-step problems',
            'Peer teaching exercises'
        ]
        
        return plan
    
    async def _calculate_learning_trajectory(
        self,
        weakness_patterns: List[WeaknessPattern],
        strength_patterns: List[StrengthPattern],
        current_score: float
    ) -> Dict[str, Any]:
        """Calculate projected learning trajectory"""
        
        # Estimate improvement potential
        total_weakness_weight = sum(wp.severity_score for wp in weakness_patterns)
        potential_improvement = min(30, total_weakness_weight * 20)  # Cap at 30 points
        
        # Calculate timeline
        weeks_needed = max(4, len(weakness_patterns) * 2)
        
        trajectory = {
            'current_score': current_score,
            'projected_improvement': potential_improvement,
            'target_score': min(100, current_score + potential_improvement),
            'estimated_weeks': weeks_needed,
            'confidence_level': 'high' if potential_improvement > 15 else 'medium',
            'milestones': self._generate_milestones(current_score, potential_improvement, weeks_needed),
            'risk_factors': self._identify_risk_factors(weakness_patterns),
            'success_factors': [sp.topic_name for sp in strength_patterns if sp.mastery_score > 0.8]
        }
        
        return trajectory
    
    def _generate_milestones(self, current_score: float, improvement: float, weeks: int) -> List[Dict]:
        """Generate learning milestones"""
        milestones = []
        
        improvement_per_week = improvement / weeks
        
        for week in range(1, weeks + 1):
            milestone_score = current_score + (improvement_per_week * week)
            milestones.append({
                'week': week,
                'target_score': round(milestone_score, 1),
                'activities': f'Week {week} focus activities',
                'assessment': f'Week {week} mini-assessment'
            })
        
        return milestones
    
    def _identify_risk_factors(self, weakness_patterns: List[WeaknessPattern]) -> List[str]:
        """Identify potential risk factors for learning"""
        risks = []
        
        high_severity_count = sum(1 for wp in weakness_patterns if wp.severity_score > 0.7)
        if high_severity_count > 3:
            risks.append('Multiple high-severity weaknesses')
        
        rushed_answers = any('rushed_answer' in wp.error_types for wp in weakness_patterns)
        if rushed_answers:
            risks.append('Time management issues')
        
        knowledge_gaps = any('knowledge_gap' in wp.error_types for wp in weakness_patterns)
        if knowledge_gaps:
            risks.append('Fundamental knowledge gaps')
        
        return risks
    
    def _get_priority_areas(self, weakness_patterns: List[WeaknessPattern]) -> List[str]:
        """Get top priority areas for immediate attention"""
        sorted_patterns = sorted(weakness_patterns, 
                               key=lambda x: x.remediation_priority, 
                               reverse=True)
        return [wp.topic_name for wp in sorted_patterns[:3]]
    
    def _generate_next_steps(self, learning_gaps: List[LearningGap], remediation_plan: Dict) -> List[str]:
        """Generate immediate next steps"""
        next_steps = [
            "Start with Phase 1 foundation activities",
            f"Focus on {learning_gaps[0].title if learning_gaps else 'basic concepts'}",
            "Watch recommended videos for weak areas",
            "Complete prerequisite concept review",
            "Schedule regular practice sessions"
        ]
        
        return next_steps
    
    async def _save_analysis_results(self, diagnostic_test_id: str, analysis_result: Dict) -> None:
        """Save analysis results to database"""
        try:
            query = text("""
                INSERT INTO diagnostic_analytics (
                    id, diagnostic_test_id, analysis_data, 
                    weakness_count, strength_count, created_at
                ) VALUES (
                    gen_random_uuid(), :diagnostic_test_id, :analysis_data,
                    :weakness_count, :strength_count, CURRENT_TIMESTAMP
                ) ON CONFLICT (diagnostic_test_id) DO UPDATE SET
                    analysis_data = EXCLUDED.analysis_data,
                    weakness_count = EXCLUDED.weakness_count,
                    strength_count = EXCLUDED.strength_count,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            self.db.execute(query, {
                'diagnostic_test_id': diagnostic_test_id,
                'analysis_data': json.dumps(analysis_result),
                'weakness_count': len(analysis_result.get('weakness_patterns', [])),
                'strength_count': len(analysis_result.get('strength_patterns', []))
            })
            
            self.db.commit()
            logger.info(f"✅ Analysis results saved for diagnostic {diagnostic_test_id}")
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            self.db.rollback()
    
    async def get_saved_analysis(self, diagnostic_test_id: str) -> Dict[str, Any]:
        """Retrieve saved analysis results"""
        try:
            query = text("""
                SELECT analysis_data, weakness_count, strength_count, created_at
                FROM diagnostic_analytics
                WHERE diagnostic_test_id = :diagnostic_test_id
            """)
            
            result = self.db.execute(query, {'diagnostic_test_id': diagnostic_test_id}).first()
            
            if result:
                analysis_data = json.loads(result[0])
                analysis_data['saved_metadata'] = {
                    'weakness_count': result[1],
                    'strength_count': result[2],
                    'created_at': result[3].isoformat() if result[3] else None
                }
                return {'success': True, 'analysis': analysis_data}
            else:
                return {'success': False, 'error': 'Analysis not found'}
                
        except Exception as e:
            logger.error(f"Error retrieving saved analysis: {e}")
            return {'success': False, 'error': str(e)}