#!/usr/bin/env python3
"""
Schema Guard - Protector inteligente de la base de datos
Previene desincronizaciones entre modelos y BD
"""

import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from typing import Dict, List, Set
import asyncio
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaGuard:
    """Protector de esquema de base de datos"""
    
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)
        self.last_check = time.time()
        self.check_interval = 300  # 5 minutos
        self.health_status = "healthy"
        self.issues_count = 0
        
    async def start_monitoring(self):
        """Iniciar monitoreo continuo"""
        logger.info("🛡️ Schema Guard iniciado - Monitoreando BD cada 5 minutos")
        
        while True:
            try:
                await self.check_schema_integrity()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error en Schema Guard: {e}")
                self.health_status = "error"
                await asyncio.sleep(60)  # Esperar 1 minuto en caso de error
    
    async def check_schema_integrity(self):
        """Verificar integridad del esquema"""
        current_time = time.time()
        
        # Solo verificar si han pasado 5 minutos
        if current_time - self.last_check < self.check_interval:
            return
        
        logger.info("🔍 Verificando integridad del esquema...")
        
        # Verificar tablas críticas
        critical_issues = await self._check_critical_tables()
        
        # Verificar foreign keys
        fk_issues = await self._check_foreign_keys()
        
        # Verificar columnas críticas
        column_issues = await self._check_critical_columns()
        
        # Verificar índices
        index_issues = await self._check_critical_indexes()
        
        # Reportar problemas
        total_issues = len(critical_issues) + len(fk_issues) + len(column_issues) + len(index_issues)
        
        if total_issues > 0:
            self.health_status = "warning"
            self.issues_count = total_issues
            await self._report_issues(critical_issues, fk_issues, column_issues, index_issues)
        else:
            self.health_status = "healthy"
            self.issues_count = 0
            logger.info("✅ Esquema de BD perfecto")
        
        self.last_check = current_time
    
    async def _check_critical_tables(self) -> List[str]:
        """Verificar tablas críticas"""
        issues = []
        critical_tables = [
            'users', 'subjects', 'topics', 'questions',
            'diagnostic_tests', 'diagnostic_test_answers',
            'battles', 'battle_answers', 'study_plans',
            'achievements', 'user_achievements', 'guilds',
            'user_guilds', 'daily_quests', 'user_daily_quests'
        ]
        
        for table in critical_tables:
            if not self.inspector.has_table(table):
                issues.append(f"Tabla crítica faltante: {table}")
        
        return issues
    
    async def _check_foreign_keys(self) -> List[str]:
        """Verificar foreign keys críticas"""
        issues = []
        
        # Verificar FK de diagnostic_test_answers
        if self.inspector.has_table('diagnostic_test_answers'):
            fks = self.inspector.get_foreign_keys('diagnostic_test_answers')
            test_id_fk = any(
                'test_id' in fk['constrained_columns'] and 
                fk['referred_table'] == 'diagnostic_tests'
                for fk in fks
            )
            
            if not test_id_fk:
                issues.append("FK faltante: diagnostic_test_answers.test_id -> diagnostic_tests.id")
        
        # Verificar FK de questions
        if self.inspector.has_table('questions'):
            fks = self.inspector.get_foreign_keys('questions')
            topic_id_fk = any(
                'topic_id' in fk['constrained_columns'] and 
                fk['referred_table'] == 'topics'
                for fk in fks
            )
            
            if not topic_id_fk:
                issues.append("FK faltante: questions.topic_id -> topics.id")
        
        return issues
    
    async def _check_critical_columns(self) -> List[str]:
        """Verificar columnas críticas"""
        issues = []
        
        # Verificar columna test_id
        if self.inspector.has_table('diagnostic_test_answers'):
            columns = [col['name'] for col in self.inspector.get_columns('diagnostic_test_answers')]
            if 'test_id' not in columns:
                issues.append("Columna crítica faltante: diagnostic_test_answers.test_id")
        
        # Verificar columna user_id en tablas críticas
        user_tables = ['diagnostic_tests', 'battles', 'study_plans']
        for table in user_tables:
            if self.inspector.has_table(table):
                columns = [col['name'] for col in self.inspector.get_columns(table)]
                if 'user_id' not in columns:
                    issues.append(f"Columna crítica faltante: {table}.user_id")
        
        return issues
    
    async def _check_critical_indexes(self) -> List[str]:
        """Verificar índices críticos"""
        issues = []
        
        # Verificar índices en tablas críticas
        critical_indexes = [
            ('users', 'email'),
            ('questions', 'topic_id'),
            ('diagnostic_test_answers', 'test_id'),
            ('battles', 'user_id')
        ]
        
        for table, column in critical_indexes:
            if self.inspector.has_table(table):
                indexes = self.inspector.get_indexes(table)
                column_indexed = any(
                    column in idx['column_names'] 
                    for idx in indexes
                )
                
                if not column_indexed:
                    issues.append(f"Índice faltante: {table}.{column}")
        
        return issues
    
    async def _report_issues(self, table_issues: List[str], fk_issues: List[str], column_issues: List[str], index_issues: List[str]):
        """Reportar problemas encontrados"""
        logger.warning("🚨 PROBLEMAS DE ESQUEMA DETECTADOS:")
        
        if table_issues:
            for issue in table_issues:
                logger.error(f"  ❌ {issue}")
        
        if fk_issues:
            for issue in fk_issues:
                logger.error(f"  ❌ {issue}")
        
        if column_issues:
            for issue in column_issues:
                logger.error(f"  ❌ {issue}")
        
        if index_issues:
            for issue in index_issues:
                logger.error(f"  ❌ {issue}")
        
        logger.warning("🔧 Ejecuta el script de reparación inmediatamente")
        
        # Aquí podrías enviar notificaciones (email, Slack, etc.)
        await self._send_alert(table_issues + fk_issues + column_issues + index_issues)
    
    async def _send_alert(self, issues: List[str]):
        """Enviar alerta (implementar según necesidades)"""
        # Ejemplo: enviar a Slack, email, etc.
        logger.info(f"📢 Alerta enviada: {len(issues)} problemas detectados")
    
    def get_health_status(self) -> Dict:
        """Obtener estado de salud del Schema Guard"""
        return {
            "status": self.health_status,
            "issues_count": self.issues_count,
            "last_check": datetime.fromtimestamp(self.last_check).isoformat(),
            "check_interval": self.check_interval
        }
    
    async def force_check(self):
        """Forzar verificación inmediata"""
        logger.info("🔍 Verificación forzada del esquema...")
        await self.check_schema_integrity()

# Integración en main.py
def setup_schema_guard(app, engine):
    """Configurar Schema Guard en la aplicación"""
    guard = SchemaGuard(engine)
    
    @app.on_event("startup")
    async def start_schema_guard():
        asyncio.create_task(guard.start_monitoring())
    
    return guard
