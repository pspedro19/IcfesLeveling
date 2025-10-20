#!/usr/bin/env python3
"""
Comprehensive Video Recommendation Validation System
Tests the precision and effectiveness of weakness-video matching algorithms
"""

import asyncio
import json
import sqlite3
import logging
import sys
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import random

# Add the backend app to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

from app.core.database import SessionLocal
from app.services.video_question_matching_service import VideoQuestionMatchingService, StudentWeakness
from app.services.diagnostic_weakness_analyzer import DiagnosticWeaknessAnalyzer
from app.models.youtube_catalog import YoutubeCatalog
from app.models.question import Question
from app.models.topic import Topic
from app.models.subject import Subject

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    test_name: str
    subject: str
    weakness_type: str
    student_scenario: str
    recommended_videos: List[Dict]
    precision_score: float
    relevance_score: float
    educational_quality_score: float
    total_score: float
    notes: str
    passed: bool

@dataclass
class SubjectTestScenario:
    subject_name: str
    topic: str
    weakness_pattern: str
    failed_questions_simulation: List[str]
    expected_video_keywords: List[str]
    difficulty_level: float

class VideoRecommendationValidator:
    """
    Comprehensive validator for video recommendation precision and effectiveness
    """

    def __init__(self):
        self.db = SessionLocal()
        self.matching_service = VideoQuestionMatchingService(self.db)
        self.weakness_analyzer = DiagnosticWeaknessAnalyzer(self.db)
        self.validation_results = []

        # Define realistic test scenarios for each subject
        self.test_scenarios = {
            'Math': [
                SubjectTestScenario(
                    subject_name='Matemáticas',
                    topic='Algebra',
                    weakness_pattern='conceptual_misunderstanding',
                    failed_questions_simulation=['Solve for x: 2x + 5 = 13', 'Factor: x² - 9'],
                    expected_video_keywords=['algebra', 'ecuaciones', 'factorización', 'variable'],
                    difficulty_level=0.4
                ),
                SubjectTestScenario(
                    subject_name='Matemáticas',
                    topic='Geometry',
                    weakness_pattern='procedural_error',
                    failed_questions_simulation=['Calculate area of triangle', 'Find perimeter of rectangle'],
                    expected_video_keywords=['geometría', 'área', 'perímetro', 'triángulo'],
                    difficulty_level=0.3
                ),
                SubjectTestScenario(
                    subject_name='Matemáticas',
                    topic='Statistics',
                    weakness_pattern='calculation_error',
                    failed_questions_simulation=['Calculate mean', 'Find standard deviation'],
                    expected_video_keywords=['estadística', 'media', 'desviación', 'datos'],
                    difficulty_level=0.6
                )
            ],
            'Spanish': [
                SubjectTestScenario(
                    subject_name='Lenguaje',
                    topic='Reading Comprehension',
                    weakness_pattern='interpretation_error',
                    failed_questions_simulation=['Identify main idea', 'Infer author\'s purpose'],
                    expected_video_keywords=['comprensión', 'lectura', 'idea principal', 'interpretación'],
                    difficulty_level=0.5
                ),
                SubjectTestScenario(
                    subject_name='Lenguaje',
                    topic='Grammar',
                    weakness_pattern='procedural_error',
                    failed_questions_simulation=['Identify verb tense', 'Correct punctuation'],
                    expected_video_keywords=['gramática', 'verbos', 'puntuación', 'sintaxis'],
                    difficulty_level=0.4
                )
            ],
            'Science': [
                SubjectTestScenario(
                    subject_name='Ciencias Naturales',
                    topic='Chemistry',
                    weakness_pattern='conceptual_misunderstanding',
                    failed_questions_simulation=['Balance chemical equation', 'Calculate molarity'],
                    expected_video_keywords=['química', 'ecuaciones', 'molarity', 'reacciones'],
                    difficulty_level=0.7
                ),
                SubjectTestScenario(
                    subject_name='Ciencias Naturales',
                    topic='Physics',
                    weakness_pattern='application_error',
                    failed_questions_simulation=['Calculate velocity', 'Find force'],
                    expected_video_keywords=['física', 'velocidad', 'fuerza', 'movimiento'],
                    difficulty_level=0.6
                )
            ],
            'Social Studies': [
                SubjectTestScenario(
                    subject_name='Ciencias Sociales',
                    topic='Geography',
                    weakness_pattern='knowledge_gap',
                    failed_questions_simulation=['Identify capitals', 'Locate countries'],
                    expected_video_keywords=['geografía', 'capitales', 'países', 'ubicación'],
                    difficulty_level=0.3
                ),
                SubjectTestScenario(
                    subject_name='Ciencias Sociales',
                    topic='History',
                    weakness_pattern='interpretation_error',
                    failed_questions_simulation=['Analyze historical event', 'Compare time periods'],
                    expected_video_keywords=['historia', 'eventos', 'análisis', 'cronología'],
                    difficulty_level=0.5
                )
            ],
            'English': [
                SubjectTestScenario(
                    subject_name='Inglés',
                    topic='Grammar',
                    weakness_pattern='procedural_error',
                    failed_questions_simulation=['Past tense formation', 'Subject-verb agreement'],
                    expected_video_keywords=['grammar', 'past tense', 'verbs', 'agreement'],
                    difficulty_level=0.4
                ),
                SubjectTestScenario(
                    subject_name='Inglés',
                    topic='Vocabulary',
                    weakness_pattern='knowledge_gap',
                    failed_questions_simulation=['Word meanings', 'Synonyms'],
                    expected_video_keywords=['vocabulary', 'words', 'meaning', 'synonyms'],
                    difficulty_level=0.3
                )
            ]
        }

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive validation of the video recommendation system
        """
        logger.info("🚀 Starting comprehensive video recommendation validation...")

        validation_report = {
            'validation_timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'overall_score': 0.0,
            'subject_results': {},
            'detailed_results': [],
            'recommendations': [],
            'system_health': {}
        }

        # 1. Test database connectivity and data availability
        system_health = await self._test_system_health()
        validation_report['system_health'] = system_health

        if not system_health['database_connected']:
            logger.error("❌ Database connection failed. Cannot proceed with validation.")
            return validation_report

        # 2. Test each subject's scenarios
        for subject, scenarios in self.test_scenarios.items():
            logger.info(f"🧪 Testing {subject} scenarios...")
            subject_results = await self._test_subject_scenarios(subject, scenarios)
            validation_report['subject_results'][subject] = subject_results
            validation_report['detailed_results'].extend(subject_results['test_results'])

        # 3. Calculate overall metrics
        validation_report = await self._calculate_overall_metrics(validation_report)

        # 4. Generate recommendations for improvement
        validation_report['recommendations'] = await self._generate_improvement_recommendations(validation_report)

        # 5. Save validation report
        await self._save_validation_report(validation_report)

        return validation_report

    async def _test_system_health(self) -> Dict[str, Any]:
        """Test system health and data availability"""
        health = {
            'database_connected': False,
            'videos_available': 0,
            'questions_available': 0,
            'subjects_available': 0,
            'topics_available': 0,
            'video_quality_metrics': {}
        }

        try:
            # Test database connectivity
            subjects = self.db.query(Subject).all()
            health['database_connected'] = True
            health['subjects_available'] = len(subjects)

            # Count available data
            videos = self.db.query(YoutubeCatalog).filter(YoutubeCatalog.is_processed == True).all()
            health['videos_available'] = len(videos)

            questions = self.db.query(Question).all()
            health['questions_available'] = len(questions)

            topics = self.db.query(Topic).all()
            health['topics_available'] = len(topics)

            # Analyze video quality metrics
            if videos:
                health['video_quality_metrics'] = {
                    'avg_duration': sum(v.duration_seconds or 0 for v in videos) / len(videos),
                    'videos_with_description': sum(1 for v in videos if v.description),
                    'videos_with_transcript': sum(1 for v in videos if v.transcript),
                    'avg_educational_rating': sum(v.educational_rating or 0 for v in videos) / len(videos)
                }

            logger.info(f"✅ System health check passed: {health['videos_available']} videos, {health['questions_available']} questions")

        except Exception as e:
            logger.error(f"❌ System health check failed: {e}")
            health['error'] = str(e)

        return health

    async def _test_subject_scenarios(self, subject: str, scenarios: List[SubjectTestScenario]) -> Dict[str, Any]:
        """Test all scenarios for a specific subject"""
        subject_results = {
            'subject': subject,
            'total_scenarios': len(scenarios),
            'passed_scenarios': 0,
            'average_score': 0.0,
            'test_results': []
        }

        total_score = 0.0

        for scenario in scenarios:
            logger.info(f"🔍 Testing scenario: {subject} - {scenario.topic} - {scenario.weakness_pattern}")

            # Create simulated student weakness
            weakness = await self._create_simulated_weakness(scenario)

            # Get video recommendations
            recommendations = await self._get_recommendations_for_weakness(weakness)

            # Validate recommendations
            validation_result = await self._validate_recommendations(scenario, recommendations)

            subject_results['test_results'].append(asdict(validation_result))

            if validation_result.passed:
                subject_results['passed_scenarios'] += 1

            total_score += validation_result.total_score

        subject_results['average_score'] = total_score / len(scenarios) if scenarios else 0.0

        logger.info(f"📊 {subject} results: {subject_results['passed_scenarios']}/{subject_results['total_scenarios']} passed, avg score: {subject_results['average_score']:.2f}")

        return subject_results

    async def _create_simulated_weakness(self, scenario: SubjectTestScenario) -> StudentWeakness:
        """Create a simulated student weakness based on test scenario"""

        # Try to find a real question from the database that matches the scenario
        question = self.db.query(Question).join(Topic).join(Subject).filter(
            Subject.name.ilike(f'%{scenario.subject_name}%'),
            Topic.name.ilike(f'%{scenario.topic}%')
        ).first()

        if not question:
            # If no real question found, create a simulated one
            question_id = f"sim_{random.randint(1000, 9999)}"
            topic_id = None
            subject_id = None
        else:
            question_id = str(question.id)
            topic_id = question.topic_id
            subject_id = question.subject_id

        weakness = StudentWeakness(
            question_id=question_id,
            topic_id=topic_id,
            subject_id=subject_id,
            error_pattern=scenario.weakness_pattern,
            distractor_chosen="B",  # Simulated chosen answer
            difficulty_level=scenario.difficulty_level,
            frequency=2,  # Failed 2 times
            last_failed=datetime.now() - timedelta(days=1)
        )

        return weakness

    async def _get_recommendations_for_weakness(self, weakness: StudentWeakness) -> List[Tuple]:
        """Get video recommendations for a simulated weakness"""
        try:
            matching_videos = await self.matching_service.find_matching_videos(weakness, limit=10)
            return matching_videos
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    async def _validate_recommendations(
        self,
        scenario: SubjectTestScenario,
        recommendations: List[Tuple]
    ) -> ValidationResult:
        """Validate the quality and precision of video recommendations"""

        if not recommendations:
            return ValidationResult(
                test_name=f"{scenario.subject_name}_{scenario.topic}_{scenario.weakness_pattern}",
                subject=scenario.subject_name,
                weakness_type=scenario.weakness_pattern,
                student_scenario=f"Student fails {scenario.topic} questions with {scenario.weakness_pattern}",
                recommended_videos=[],
                precision_score=0.0,
                relevance_score=0.0,
                educational_quality_score=0.0,
                total_score=0.0,
                notes="No recommendations generated",
                passed=False
            )

        # Extract video data for analysis
        video_data = []
        precision_scores = []
        relevance_scores = []
        quality_scores = []

        for video, score in recommendations:
            video_info = {
                'title': video.title,
                'description': video.description[:200] if video.description else '',
                'tema_principal': video.tema_principal,
                'area_evaluada': video.area_evaluada,
                'duration_seconds': video.duration_seconds,
                'matching_score': score.total_score,
                'difficulty_match': score.difficulty_proximity
            }
            video_data.append(video_info)

            # Calculate precision score (how well video matches the specific weakness)
            precision = await self._calculate_precision_score(video, scenario)
            precision_scores.append(precision)

            # Calculate relevance score (how relevant video content is)
            relevance = await self._calculate_relevance_score(video, scenario)
            relevance_scores.append(relevance)

            # Calculate educational quality score
            quality = await self._calculate_educational_quality_score(video)
            quality_scores.append(quality)

        # Calculate overall scores
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        total_score = (avg_precision * 0.4 + avg_relevance * 0.4 + avg_quality * 0.2)

        # Determine if test passed (threshold: 0.6)
        passed = total_score >= 0.6 and len(recommendations) > 0

        # Generate notes
        notes = await self._generate_validation_notes(scenario, recommendations, avg_precision, avg_relevance, avg_quality)

        return ValidationResult(
            test_name=f"{scenario.subject_name}_{scenario.topic}_{scenario.weakness_pattern}",
            subject=scenario.subject_name,
            weakness_type=scenario.weakness_pattern,
            student_scenario=f"Student fails {scenario.topic} questions showing {scenario.weakness_pattern}",
            recommended_videos=video_data,
            precision_score=avg_precision,
            relevance_score=avg_relevance,
            educational_quality_score=avg_quality,
            total_score=total_score,
            notes=notes,
            passed=passed
        )

    async def _calculate_precision_score(self, video: YoutubeCatalog, scenario: SubjectTestScenario) -> float:
        """Calculate how precisely the video targets the specific weakness"""
        score = 0.0

        video_text = f"{video.title} {video.description or ''} {video.tema_principal or ''}".lower()

        # Check for expected keywords
        keyword_matches = sum(1 for keyword in scenario.expected_video_keywords if keyword.lower() in video_text)
        keyword_score = keyword_matches / len(scenario.expected_video_keywords) if scenario.expected_video_keywords else 0.0
        score += keyword_score * 0.5

        # Check topic alignment
        if video.tema_principal and scenario.topic.lower() in video.tema_principal.lower():
            score += 0.3

        # Check weakness pattern addressing
        weakness_keywords = {
            'conceptual_misunderstanding': ['concepto', 'teoría', 'definición', 'fundamento'],
            'procedural_error': ['paso a paso', 'procedimiento', 'método', 'proceso'],
            'calculation_error': ['cálculo', 'operación', 'resolver', 'ejercicio'],
            'interpretation_error': ['interpretación', 'análisis', 'comprensión'],
            'application_error': ['aplicación', 'ejemplo', 'práctica', 'uso'],
            'knowledge_gap': ['básico', 'introducción', 'fundamentos', 'conceptos']
        }

        pattern_keywords = weakness_keywords.get(scenario.weakness_pattern, [])
        pattern_matches = sum(1 for keyword in pattern_keywords if keyword in video_text)
        if pattern_keywords:
            score += (pattern_matches / len(pattern_keywords)) * 0.2

        return min(1.0, score)

    async def _calculate_relevance_score(self, video: YoutubeCatalog, scenario: SubjectTestScenario) -> float:
        """Calculate how relevant the video content is to the learning need"""
        score = 0.0

        # Duration appropriateness (5-30 minutes is ideal)
        duration = video.duration_seconds or 0
        if 300 <= duration <= 1800:  # 5-30 minutes
            score += 0.2
        elif 120 <= duration <= 3600:  # 2-60 minutes
            score += 0.1

        # Content completeness
        if video.description and len(video.description) > 100:
            score += 0.2

        if video.transcript and len(video.transcript) > 200:
            score += 0.2

        # Educational rating
        if video.educational_rating:
            score += (video.educational_rating / 5.0) * 0.2

        # View count and engagement (indicates community validation)
        if video.view_count:
            # Logarithmic scale for view count
            import math
            view_score = min(0.2, math.log10(max(1, video.view_count)) / 7.0 * 0.2)
            score += view_score

        return min(1.0, score)

    async def _calculate_educational_quality_score(self, video: YoutubeCatalog) -> float:
        """Calculate the educational quality of the video"""
        score = 0.0

        # Instructor verification
        if video.instructor_verified:
            score += 0.3

        # Educational rating
        if video.educational_rating:
            score += (video.educational_rating / 5.0) * 0.3

        # Content structure indicators
        video_text = f"{video.title} {video.description or ''}".lower()

        # Look for structured content indicators
        structure_indicators = ['paso', 'ejemplo', 'ejercicio', 'práctica', 'explicación', 'tutorial']
        structure_matches = sum(1 for indicator in structure_indicators if indicator in video_text)
        score += min(0.2, structure_matches * 0.05)

        # Length appropriateness for educational content
        duration = video.duration_seconds or 0
        if 600 <= duration <= 2400:  # 10-40 minutes is ideal for educational content
            score += 0.2
        elif 300 <= duration <= 3600:  # 5-60 minutes is acceptable
            score += 0.1

        return min(1.0, score)

    async def _generate_validation_notes(
        self,
        scenario: SubjectTestScenario,
        recommendations: List[Tuple],
        precision: float,
        relevance: float,
        quality: float
    ) -> str:
        """Generate detailed notes about the validation results"""
        notes = []

        notes.append(f"Scenario: {scenario.subject_name} - {scenario.topic} with {scenario.weakness_pattern}")
        notes.append(f"Generated {len(recommendations)} recommendations")
        notes.append(f"Precision: {precision:.2f}, Relevance: {relevance:.2f}, Quality: {quality:.2f}")

        if recommendations:
            top_video = recommendations[0][0]
            notes.append(f"Top recommendation: '{top_video.title}' (Score: {recommendations[0][1].total_score:.2f})")

        # Add specific feedback
        if precision < 0.5:
            notes.append("⚠️ Low precision - videos may not specifically target the identified weakness")
        if relevance < 0.5:
            notes.append("⚠️ Low relevance - video content may not be appropriate for learning need")
        if quality < 0.5:
            notes.append("⚠️ Low quality - videos may lack educational structure or verification")

        return " | ".join(notes)

    async def _calculate_overall_metrics(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall validation metrics"""
        all_results = validation_report['detailed_results']

        if not all_results:
            return validation_report

        # Count totals
        validation_report['total_tests'] = len(all_results)
        validation_report['passed_tests'] = sum(1 for result in all_results if result['passed'])
        validation_report['failed_tests'] = validation_report['total_tests'] - validation_report['passed_tests']

        # Calculate overall score
        total_score = sum(result['total_score'] for result in all_results)
        validation_report['overall_score'] = total_score / len(all_results)

        # Calculate metric averages
        validation_report['average_precision'] = sum(result['precision_score'] for result in all_results) / len(all_results)
        validation_report['average_relevance'] = sum(result['relevance_score'] for result in all_results) / len(all_results)
        validation_report['average_quality'] = sum(result['educational_quality_score'] for result in all_results) / len(all_results)

        # Pass rate
        validation_report['pass_rate'] = validation_report['passed_tests'] / validation_report['total_tests']

        return validation_report

    async def _generate_improvement_recommendations(self, validation_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving the video recommendation system"""
        recommendations = []

        overall_score = validation_report.get('overall_score', 0.0)
        avg_precision = validation_report.get('average_precision', 0.0)
        avg_relevance = validation_report.get('average_relevance', 0.0)
        avg_quality = validation_report.get('average_quality', 0.0)

        # Overall system recommendations
        if overall_score < 0.7:
            recommendations.append("🚨 CRITICAL: Overall system performance below acceptable threshold (0.7)")

        # Precision recommendations
        if avg_precision < 0.6:
            recommendations.append("🎯 Improve weakness detection precision: Enhance keyword matching and semantic analysis")
            recommendations.append("📝 Add more specific metadata to video catalog (tags, learning objectives)")
            recommendations.append("🔍 Implement better error pattern classification")

        # Relevance recommendations
        if avg_relevance < 0.6:
            recommendations.append("📚 Improve video content analysis: Add better quality metrics")
            recommendations.append("⏱️ Filter videos by appropriate duration for educational content")
            recommendations.append("✅ Implement instructor verification system")

        # Quality recommendations
        if avg_quality < 0.6:
            recommendations.append("🏆 Enhance video quality scoring: Include engagement metrics")
            recommendations.append("📖 Require better video descriptions and transcripts")
            recommendations.append("👨‍🏫 Partner with verified educational content creators")

        # Subject-specific recommendations
        subject_results = validation_report.get('subject_results', {})
        for subject, results in subject_results.items():
            if results['average_score'] < 0.6:
                recommendations.append(f"📊 {subject}: Below threshold - review video catalog coverage")

        # System health recommendations
        system_health = validation_report.get('system_health', {})
        if system_health.get('videos_available', 0) < 100:
            recommendations.append("📹 Expand video catalog: Current collection may be insufficient")

        return recommendations

    async def _save_validation_report(self, validation_report: Dict[str, Any]) -> None:
        """Save validation report to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/root/IcfesLeveling/video_recommendation_validation_report_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(validation_report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"✅ Validation report saved: {filename}")

        except Exception as e:
            logger.error(f"❌ Failed to save validation report: {e}")

    def __del__(self):
        """Clean up database connection"""
        try:
            self.db.close()
        except:
            pass

async def main():
    """Run the comprehensive video recommendation validation"""
    print("🚀 Starting Video Recommendation System Validation")
    print("=" * 80)

    validator = VideoRecommendationValidator()

    try:
        validation_report = await validator.run_comprehensive_validation()

        # Print summary
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Overall Score: {validation_report.get('overall_score', 0):.2f}/1.0")
        print(f"Pass Rate: {validation_report.get('pass_rate', 0)*100:.1f}%")
        print(f"Tests Passed: {validation_report.get('passed_tests', 0)}/{validation_report.get('total_tests', 0)}")

        print(f"\nMetric Breakdown:")
        print(f"  • Precision: {validation_report.get('average_precision', 0):.2f}")
        print(f"  • Relevance: {validation_report.get('average_relevance', 0):.2f}")
        print(f"  • Quality: {validation_report.get('average_quality', 0):.2f}")

        # Print subject results
        print(f"\n📚 SUBJECT PERFORMANCE")
        print("-" * 40)
        for subject, results in validation_report.get('subject_results', {}).items():
            status = "✅ PASS" if results['average_score'] >= 0.6 else "❌ FAIL"
            print(f"{subject}: {results['average_score']:.2f} ({results['passed_scenarios']}/{results['total_scenarios']}) {status}")

        # Print recommendations
        recommendations = validation_report.get('recommendations', [])
        if recommendations:
            print(f"\n🔧 IMPROVEMENT RECOMMENDATIONS")
            print("-" * 40)
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")

        # Overall assessment
        overall_score = validation_report.get('overall_score', 0)
        if overall_score >= 0.8:
            print(f"\n🎉 EXCELLENT: Video recommendation system performs very well!")
        elif overall_score >= 0.7:
            print(f"\n✅ GOOD: Video recommendation system meets quality standards.")
        elif overall_score >= 0.6:
            print(f"\n⚠️ ACCEPTABLE: Video recommendation system needs minor improvements.")
        else:
            print(f"\n🚨 CRITICAL: Video recommendation system requires significant improvements.")

        return validation_report

    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(main())