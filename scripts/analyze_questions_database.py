#!/usr/bin/env python3
"""
ICFES Database Questions Analysis Script
Analyzes questions in the database to identify fake/synthetic content vs real ICFES questions
"""

import os
import sys
import psycopg2
import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

# Add the backend app to the path
sys.path.append('/root/IcfesLeveling/apps/backend')

@dataclass
class QuestionAnalysis:
    id: int
    text: str
    subject: str
    difficulty: str
    is_fake_probability: float
    fake_indicators: List[str]
    raw_data: Dict[str, Any]

class ICFESQuestionAnalyzer:
    def __init__(self):
        # Common fake/synthetic question patterns
        self.fake_patterns = [
            # Mathematical patterns that are too simple/obvious
            r'2x\s*\+\s*3\s*=\s*11',
            r'x\s*=\s*4',
            r'triángulo rectángulo.*catetos.*3.*4',
            r'hipotenusa.*5',
            r'resolver.*ecuación.*x\s*=',

            # Too simplistic language patterns
            r'^¿Cuál es.*\?$',
            r'^¿Qué.*\?$',
            r'^Encuentra.*$',
            r'^Calcula.*$',
            r'^Resuelve.*$',

            # Non-ICFES style patterns
            r'ejemplo.*básico',
            r'ejercicio.*simple',
            r'pregunta.*fácil',
            r'test.*question',

            # Overly direct answer patterns
            r'respuesta.*correcta.*es',
            r'la.*opción.*correcta',

            # Mathematical expressions that are too textbook-like
            r'Sean.*a.*y.*b.*números',
            r'Dado.*que.*x.*es.*un.*número',
            r'Si.*tenemos.*la.*función',

            # Biology/Science patterns that are too basic
            r'célula.*básica',
            r'organismo.*simple',
            r'proceso.*básico',

            # History patterns that are too general
            r'evento.*histórico.*importante',
            r'fecha.*importante.*en.*la.*historia',

            # Language patterns that are too simple
            r'palabra.*significa',
            r'definición.*de',
            r'concepto.*básico',
        ]

        # Real ICFES indicators
        self.real_indicators = [
            # Complex mathematical reasoning
            r'función.*inversa',
            r'derivada.*de.*la.*función',
            r'integral.*definida',
            r'límite.*cuando.*x.*tiende',
            r'probabilidad.*condicional',
            r'distribución.*normal',

            # Complex scientific concepts
            r'equilibrio.*químico',
            r'enlace.*covalente',
            r'reacción.*redox',
            r'campo.*magnético',
            r'ley.*de.*conservación',

            # Complex biological concepts
            r'síntesis.*de.*proteínas',
            r'ciclo.*de.*Krebs',
            r'mitosis.*y.*meiosis',
            r'expresión.*génica',
            r'biodiversidad.*ecosistémica',

            # Complex historical/social concepts
            r'Revolución.*Industrial',
            r'constitución.*política',
            r'democracia.*participativa',
            r'globalización.*económica',

            # Complex language concepts
            r'función.*del.*lenguaje',
            r'cohesión.*textual',
            r'pragmática.*del.*discurso',
            r'análisis.*sintáctico',
        ]

        # Subject classifications
        self.subjects = {
            'matematicas': ['matemáticas', 'mathematics', 'math', 'álgebra', 'geometría', 'cálculo', 'estadística'],
            'ciencias_naturales': ['biología', 'química', 'física', 'biology', 'chemistry', 'physics'],
            'ciencias_sociales': ['historia', 'geografía', 'cívica', 'filosofía', 'history', 'geography'],
            'lenguaje': ['español', 'literatura', 'lenguaje', 'language', 'spanish', 'literatura'],
            'ingles': ['inglés', 'english', 'ingles']
        }

    def connect_to_database(self):
        """Connect to the PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                host="postgres",
                database="gameplay_db",
                user="gameplay",
                password="gameplay123",
                port=5432
            )
            return conn
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None

    def get_all_questions(self, conn) -> List[Dict[str, Any]]:
        """Retrieve all questions from the database"""
        cursor = conn.cursor()

        # Get table structure first
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'questions'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("Questions table structure:")
        for col, dtype in columns:
            print(f"  {col}: {dtype}")

        # Get all questions
        cursor.execute("""
            SELECT id, text, subject, difficulty, options, correct_answer,
                   explanation, topic, subtopic, cognitive_level,
                   created_at, updated_at
            FROM questions
            ORDER BY id
        """)

        questions = []
        for row in cursor.fetchall():
            questions.append({
                'id': row[0],
                'text': row[1],
                'subject': row[2],
                'difficulty': row[3],
                'options': row[4],
                'correct_answer': row[5],
                'explanation': row[6],
                'topic': row[7],
                'subtopic': row[8],
                'cognitive_level': row[9],
                'created_at': row[10],
                'updated_at': row[11]
            })

        cursor.close()
        return questions

    def analyze_question(self, question: Dict[str, Any]) -> QuestionAnalysis:
        """Analyze a single question to determine if it's fake/synthetic"""
        text = question.get('text', '').lower()
        subject = question.get('subject', '').lower()

        fake_indicators = []
        is_fake_score = 0.0

        # Check for fake patterns
        for pattern in self.fake_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                fake_indicators.append(f"Fake pattern: {pattern}")
                is_fake_score += 0.2

        # Check for real ICFES indicators (reduces fake score)
        real_indicators_found = 0
        for pattern in self.real_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                real_indicators_found += 1
                is_fake_score -= 0.15

        # Length analysis
        if len(text) < 50:
            fake_indicators.append("Question text too short")
            is_fake_score += 0.3
        elif len(text) > 500:
            fake_indicators.append("Question text unusually long")
            is_fake_score += 0.1

        # Options analysis
        options = question.get('options')
        if options:
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except:
                    pass

            if isinstance(options, list) and len(options) < 4:
                fake_indicators.append("Insufficient answer options")
                is_fake_score += 0.2

        # Subject consistency
        if not subject:
            fake_indicators.append("Missing subject classification")
            is_fake_score += 0.1

        # Difficulty analysis
        difficulty = question.get('difficulty', '').lower()
        if difficulty not in ['fácil', 'medio', 'difícil', 'easy', 'medium', 'hard', 'bajo', 'medio', 'alto']:
            fake_indicators.append("Invalid difficulty classification")
            is_fake_score += 0.1

        # Cap the score
        is_fake_score = max(0.0, min(1.0, is_fake_score))

        return QuestionAnalysis(
            id=question['id'],
            text=question['text'][:200] + "..." if len(question['text']) > 200 else question['text'],
            subject=subject,
            difficulty=difficulty,
            is_fake_probability=is_fake_score,
            fake_indicators=fake_indicators,
            raw_data=question
        )

    def generate_report(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        analyses = [self.analyze_question(q) for q in questions]

        # Statistics by subject
        subject_stats = defaultdict(lambda: {'total': 0, 'fake': 0, 'likely_fake': 0})
        fake_questions = []
        likely_fake_questions = []

        for analysis in analyses:
            subject = analysis.subject or 'unknown'
            subject_stats[subject]['total'] += 1

            if analysis.is_fake_probability >= 0.7:
                subject_stats[subject]['fake'] += 1
                fake_questions.append(analysis)
            elif analysis.is_fake_probability >= 0.4:
                subject_stats[subject]['likely_fake'] += 1
                likely_fake_questions.append(analysis)

        # Generate cleanup SQL
        fake_ids = [str(q.id) for q in fake_questions]
        likely_fake_ids = [str(q.id) for q in likely_fake_questions]

        cleanup_sql = []
        if fake_ids:
            cleanup_sql.append(f"-- Remove definitely fake questions ({len(fake_ids)} questions)")
            cleanup_sql.append(f"DELETE FROM questions WHERE id IN ({', '.join(fake_ids)});")

        if likely_fake_ids:
            cleanup_sql.append(f"-- Mark likely fake questions for review ({len(likely_fake_ids)} questions)")
            cleanup_sql.append(f"UPDATE questions SET topic = 'REVIEW_LIKELY_FAKE' WHERE id IN ({', '.join(likely_fake_ids)});")

        return {
            'total_questions': len(questions),
            'subject_statistics': dict(subject_stats),
            'fake_questions': [asdict(q) for q in fake_questions],
            'likely_fake_questions': [asdict(q) for q in likely_fake_questions],
            'cleanup_sql': cleanup_sql,
            'summary': {
                'definitely_fake': len(fake_questions),
                'likely_fake': len(likely_fake_questions),
                'probably_real': len(analyses) - len(fake_questions) - len(likely_fake_questions)
            }
        }

def main():
    analyzer = ICFESQuestionAnalyzer()

    print("Connecting to ICFES database...")
    conn = analyzer.connect_to_database()

    if not conn:
        print("Failed to connect to database")
        return

    try:
        print("Retrieving all questions...")
        questions = analyzer.get_all_questions(conn)
        print(f"Found {len(questions)} questions in database")

        print("Analyzing questions for fake/synthetic content...")
        report = analyzer.generate_report(questions)

        # Print summary
        print("\n" + "="*60)
        print("ICFES QUESTIONS DATABASE ANALYSIS REPORT")
        print("="*60)

        print(f"\nTOTAL QUESTIONS: {report['total_questions']}")

        print(f"\nSUMMARY:")
        print(f"  Definitely Fake: {report['summary']['definitely_fake']}")
        print(f"  Likely Fake: {report['summary']['likely_fake']}")
        print(f"  Probably Real: {report['summary']['probably_real']}")

        print(f"\nQUESTIONS BY SUBJECT:")
        for subject, stats in report['subject_statistics'].items():
            print(f"  {subject.upper()}:")
            print(f"    Total: {stats['total']}")
            print(f"    Fake: {stats['fake']}")
            print(f"    Likely Fake: {stats['likely_fake']}")
            print(f"    Probably Real: {stats['total'] - stats['fake'] - stats['likely_fake']}")

        print(f"\nDEFINITELY FAKE QUESTIONS ({len(report['fake_questions'])}):")
        for i, fake in enumerate(report['fake_questions'][:10], 1):  # Show first 10
            print(f"  {i}. ID {fake['id']} ({fake['subject']}):")
            print(f"     Text: {fake['text']}")
            print(f"     Fake Score: {fake['is_fake_probability']:.2f}")
            print(f"     Indicators: {', '.join(fake['fake_indicators'])}")
            print()

        if len(report['fake_questions']) > 10:
            print(f"     ... and {len(report['fake_questions']) - 10} more")

        print(f"\nLIKELY FAKE QUESTIONS ({len(report['likely_fake_questions'])}):")
        for i, likely in enumerate(report['likely_fake_questions'][:5], 1):  # Show first 5
            print(f"  {i}. ID {likely['id']} ({likely['subject']}):")
            print(f"     Text: {likely['text']}")
            print(f"     Fake Score: {likely['is_fake_probability']:.2f}")
            print(f"     Indicators: {', '.join(likely['fake_indicators'])}")
            print()

        if len(report['likely_fake_questions']) > 5:
            print(f"     ... and {len(report['likely_fake_questions']) - 5} more")

        print(f"\nCLEANUP SQL COMMANDS:")
        for sql in report['cleanup_sql']:
            print(f"  {sql}")

        # Save full report to file
        report_file = '/root/IcfesLeveling/questions_analysis_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nFull report saved to: {report_file}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()

if __name__ == "__main__":
    main()