"""
Dashboard de Visualización para el Sistema de Recomendaciones
Endpoints para generar dashboards interactivos y métricas visuales
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.master_recommendation_service import MasterRecommendationService
from app.services.weakness_analysis_service import WeaknessAnalysisService

# Crear router
router = APIRouter(prefix="/api/v2/dashboard", tags=["Recommendations Dashboard"])

# Instanciar servicios
master_service = MasterRecommendationService()
weakness_service = WeaknessAnalysisService()

# =============================================================================
# ENDPOINTS DE DASHBOARD PRINCIPAL
# =============================================================================

@router.get("/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene datos de overview principal del dashboard
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Obtener métricas del sistema
        system_health = await master_service.get_system_health_status(db)
        system_metrics = await master_service._calculate_system_metrics(db)
        
        # Obtener resumen de debilidades críticas
        critical_summary = await weakness_service.get_critical_weaknesses_summary(db)
        
        # Compilar overview
        overview_data = {
            'system_status': {
                'overall_health': system_health.get('overall_status', 'unknown'),
                'overall_score': system_health.get('overall_score', 0),
                'last_check': system_health.get('last_check'),
                'components_status': {
                    component: data.get('status', 'unknown')
                    for component, data in system_health.get('components', {}).items()
                }
            },
            'key_metrics': {
                'total_students': system_metrics.total_students_processed,
                'total_videos': system_metrics.total_videos_analyzed,
                'total_recommendations': system_metrics.total_recommendations_created,
                'system_accuracy': round(system_metrics.system_accuracy_score, 3),
                'coverage_percentage': round(system_metrics.coverage_percentage, 2)
            },
            'critical_insights': {
                'severity_breakdown': critical_summary.get('severity_breakdown', []),
                'problematic_topics': critical_summary.get('problematic_topics', [])[:5],  # Top 5
                'total_critical_students': sum(
                    item.get('unique_students', 0) 
                    for item in critical_summary.get('severity_breakdown', [])
                    if item.get('severity') == 'critical'
                )
            },
            'recent_activity': {
                'last_processing': system_metrics.last_processing_date.isoformat(),
                'processing_frequency': 'hourly',  # Configurable
                'next_scheduled': (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
        }
        
        return JSONResponse(content=overview_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard overview: {str(e)}")

@router.get("/analytics/performance")
async def get_performance_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    time_range: str = Query("30d", description="Rango de tiempo (7d, 30d, 90d)"),
    granularity: str = Query("daily", description="Granularidad (hourly, daily, weekly)")
):
    """
    Obtiene analytics de performance del sistema
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Mapear rangos de tiempo
        time_ranges = {
            '7d': 7,
            '30d': 30,
            '90d': 90
        }
        
        days_back = time_ranges.get(time_range, 30)
        
        # Simular datos de performance (en implementación real vendrían de logs/métricas)
        performance_data = {
            'time_series': generate_mock_time_series(days_back, granularity),
            'summary_stats': {
                'avg_response_time_ms': 250,
                'total_api_calls': 15240,
                'error_rate_percentage': 0.5,
                'peak_concurrent_users': 45,
                'system_uptime_percentage': 99.8
            },
            'component_performance': {
                'embeddings_generation': {
                    'avg_time_per_item_ms': 120,
                    'success_rate_percentage': 98.5,
                    'items_processed': 8500
                },
                'weakness_analysis': {
                    'refresh_frequency_minutes': 60,
                    'avg_refresh_time_ms': 3400,
                    'coverage_percentage': 95.2
                },
                'recommendation_scoring': {
                    'avg_score_calculation_ms': 45,
                    'recommendations_generated': 12300,
                    'quality_score': 0.87
                },
                'yaml_generation': {
                    'avg_generation_time_ms': 2800,
                    'plans_generated': 450,
                    'validation_success_rate': 99.1
                }
            },
            'resource_utilization': {
                'cpu_usage_percentage': 34,
                'memory_usage_percentage': 42,
                'disk_usage_percentage': 67,
                'database_connections': 12
            }
        }
        
        return JSONResponse(content=performance_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance analytics: {str(e)}")

def generate_mock_time_series(days_back: int, granularity: str) -> List[Dict[str, Any]]:
    """Genera datos de serie temporal mock para el dashboard"""
    import random
    from datetime import datetime, timedelta
    
    data_points = []
    
    if granularity == 'hourly':
        delta = timedelta(hours=1)
        points = min(days_back * 24, 168)  # Máximo 1 semana de datos por hora
    elif granularity == 'daily':
        delta = timedelta(days=1)
        points = days_back
    else:  # weekly
        delta = timedelta(weeks=1)
        points = max(1, days_back // 7)
    
    start_time = datetime.utcnow() - timedelta(days=days_back)
    
    for i in range(points):
        timestamp = start_time + (delta * i)
        data_point = {
            'timestamp': timestamp.isoformat(),
            'api_requests': random.randint(100, 800),
            'recommendations_generated': random.randint(50, 300),
            'avg_response_time_ms': random.randint(180, 400),
            'error_count': random.randint(0, 5),
            'active_students': random.randint(20, 150),
            'weakness_alerts': random.randint(0, 15)
        }
        data_points.append(data_point)
    
    return data_points

@router.get("/analytics/recommendations")
async def get_recommendations_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene analytics específicos del sistema de recomendaciones
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Obtener estadísticas de recomendaciones desde la base de datos
        from app.models.question_video_recommendations import QuestionVideoRecommendations
        from sqlalchemy import func, and_
        
        # Estadísticas generales
        total_recs = db.query(QuestionVideoRecommendations).filter(
            QuestionVideoRecommendations.is_active == True
        ).count()
        
        # Distribución por tipo
        type_distribution = db.query(
            QuestionVideoRecommendations.recommendation_type,
            func.count(QuestionVideoRecommendations.id).label('count')
        ).filter(
            QuestionVideoRecommendations.is_active == True
        ).group_by(QuestionVideoRecommendations.recommendation_type).all()
        
        # Distribución por nivel de confianza
        confidence_distribution = db.query(
            QuestionVideoRecommendations.confidence_level,
            func.count(QuestionVideoRecommendations.id).label('count')
        ).filter(
            QuestionVideoRecommendations.is_active == True
        ).group_by(QuestionVideoRecommendations.confidence_level).all()
        
        # Score promedio por tipo
        avg_scores_by_type = db.query(
            QuestionVideoRecommendations.recommendation_type,
            func.avg(QuestionVideoRecommendations.total_score).label('avg_score')
        ).filter(
            QuestionVideoRecommendations.is_active == True
        ).group_by(QuestionVideoRecommendations.recommendation_type).all()
        
        # Top videos más recomendados
        top_videos = db.query(
            QuestionVideoRecommendations.video_id,
            func.count(QuestionVideoRecommendations.id).label('recommendation_count'),
            func.avg(QuestionVideoRecommendations.total_score).label('avg_score')
        ).filter(
            QuestionVideoRecommendations.is_active == True
        ).group_by(QuestionVideoRecommendations.video_id).order_by(
            func.count(QuestionVideoRecommendations.id).desc()
        ).limit(10).all()
        
        analytics_data = {
            'summary': {
                'total_active_recommendations': total_recs,
                'avg_score_overall': float(db.query(func.avg(QuestionVideoRecommendations.total_score)).filter(
                    QuestionVideoRecommendations.is_active == True
                ).scalar() or 0),
                'high_quality_percentage': round(
                    (db.query(QuestionVideoRecommendations).filter(
                        and_(
                            QuestionVideoRecommendations.is_active == True,
                            QuestionVideoRecommendations.total_score >= 0.8
                        )
                    ).count() / total_recs * 100) if total_recs > 0 else 0, 2
                )
            },
            'distributions': {
                'by_type': [
                    {'type': row.recommendation_type, 'count': row.count}
                    for row in type_distribution
                ],
                'by_confidence': [
                    {'confidence_level': row.confidence_level, 'count': row.count}
                    for row in confidence_distribution
                ]
            },
            'quality_metrics': {
                'avg_scores_by_type': [
                    {'type': row.recommendation_type, 'avg_score': round(float(row.avg_score), 3)}
                    for row in avg_scores_by_type
                ]
            },
            'top_content': {
                'most_recommended_videos': [
                    {
                        'video_id': row.video_id,
                        'recommendation_count': row.recommendation_count,
                        'avg_score': round(float(row.avg_score), 3)
                    }
                    for row in top_videos
                ]
            }
        }
        
        return JSONResponse(content=analytics_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations analytics: {str(e)}")

@router.get("/analytics/weaknesses")
async def get_weaknesses_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene analytics del sistema de análisis de debilidades
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Obtener resumen de debilidades críticas
        critical_summary = await weakness_service.get_critical_weaknesses_summary(db)
        
        # Obtener alertas activas
        active_alerts = await weakness_service.get_active_alerts(db, limit=100)
        
        # Procesar datos para analytics
        analytics_data = {
            'overview': {
                'total_students_with_weaknesses': sum(
                    item.get('unique_students', 0) 
                    for item in critical_summary.get('severity_breakdown', [])
                ),
                'total_weaknesses_detected': sum(
                    item.get('count', 0) 
                    for item in critical_summary.get('severity_breakdown', [])
                ),
                'critical_alerts_active': len([a for a in active_alerts if a.severity == 'critical']),
                'avg_intervention_priority': round(
                    sum(a.intervention_priority_score for a in active_alerts) / len(active_alerts), 2
                ) if active_alerts else 0
            },
            'severity_analysis': critical_summary.get('severity_breakdown', []),
            'problematic_areas': {
                'subjects': {},
                'topics': critical_summary.get('problematic_topics', [])
            },
            'temporal_trends': critical_summary.get('temporal_trends', []),
            'alert_distribution': {
                'by_severity': {},
                'by_type': {}
            },
            'intervention_recommendations': {
                'immediate_action_required': len([
                    a for a in active_alerts 
                    if a.intervention_priority_score > 85
                ]),
                'scheduled_interventions': len([
                    a for a in active_alerts 
                    if 70 <= a.intervention_priority_score <= 85
                ]),
                'monitoring_required': len([
                    a for a in active_alerts 
                    if a.intervention_priority_score < 70
                ])
            }
        }
        
        # Procesar distribución de alertas
        for alert in active_alerts:
            # Por severidad
            severity = alert.severity
            analytics_data['alert_distribution']['by_severity'][severity] = (
                analytics_data['alert_distribution']['by_severity'].get(severity, 0) + 1
            )
            
            # Por tipo
            alert_type = alert.alert_type.value
            analytics_data['alert_distribution']['by_type'][alert_type] = (
                analytics_data['alert_distribution']['by_type'].get(alert_type, 0) + 1
            )
        
        return JSONResponse(content=analytics_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting weaknesses analytics: {str(e)}")

# =============================================================================
# ENDPOINTS DE VISUALIZACIÓN HTML
# =============================================================================

@router.get("/html/overview", response_class=HTMLResponse)
async def get_html_dashboard(
    current_user: User = Depends(get_current_user)
):
    """
    Genera dashboard HTML interactivo
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IcfesLeveling - Dashboard de Recomendaciones v2.0</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h3 { color: #333; margin-bottom: 1rem; border-bottom: 2px solid #667eea; padding-bottom: 0.5rem; }
        .metric { display: flex; justify-content: space-between; align-items: center; margin: 0.5rem 0; }
        .metric-value { font-size: 1.5rem; font-weight: bold; color: #667eea; }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        .chart-container { position: relative; height: 300px; margin: 1rem 0; }
        .loading { text-align: center; padding: 2rem; color: #666; }
        .refresh-btn { background: #667eea; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #5a6fd8; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🎯 IcfesLeveling - Dashboard de Recomendaciones v2.0</h1>
            <p>Sistema Avanzado de Recomendaciones con IA y Análisis de Debilidades</p>
        </div>
    </div>
    
    <div class="container">
        <div style="text-align: right; margin-bottom: 1rem;">
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 Actualizar Dashboard</button>
        </div>
        
        <div class="grid">
            <!-- Estado del Sistema -->
            <div class="card">
                <h3>🏥 Estado del Sistema</h3>
                <div id="system-status" class="loading">Cargando...</div>
            </div>
            
            <!-- Métricas Clave -->
            <div class="card">
                <h3>📊 Métricas Clave</h3>
                <div id="key-metrics" class="loading">Cargando...</div>
            </div>
            
            <!-- Alertas Críticas -->
            <div class="card">
                <h3>🚨 Alertas Críticas</h3>
                <div id="critical-alerts" class="loading">Cargando...</div>
            </div>
        </div>
        
        <div class="grid">
            <!-- Gráfico de Performance -->
            <div class="card">
                <h3>📈 Performance del Sistema</h3>
                <div class="chart-container">
                    <canvas id="performance-chart"></canvas>
                </div>
            </div>
            
            <!-- Distribución de Recomendaciones -->
            <div class="card">
                <h3>🎯 Distribución de Recomendaciones</h3>
                <div class="chart-container">
                    <canvas id="recommendations-chart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <!-- Análisis de Debilidades -->
            <div class="card">
                <h3>⚠️ Análisis de Debilidades</h3>
                <div id="weaknesses-analysis" class="loading">Cargando...</div>
            </div>
            
            <!-- Top Contenido -->
            <div class="card">
                <h3>🏆 Top Contenido Recomendado</h3>
                <div id="top-content" class="loading">Cargando...</div>
            </div>
        </div>
    </div>
    
    <script>
        let performanceChart, recommendationsChart;
        
        async function loadDashboardData() {
            try {
                // Cargar datos del overview
                const overviewResponse = await fetch('/api/v2/dashboard/overview');
                const overviewData = await overviewResponse.json();
                
                // Actualizar estado del sistema
                updateSystemStatus(overviewData.system_status);
                
                // Actualizar métricas clave
                updateKeyMetrics(overviewData.key_metrics);
                
                // Actualizar alertas críticas
                updateCriticalAlerts(overviewData.critical_insights);
                
                // Cargar analytics de performance
                const performanceResponse = await fetch('/api/v2/dashboard/analytics/performance');
                const performanceData = await performanceResponse.json();
                updatePerformanceChart(performanceData);
                
                // Cargar analytics de recomendaciones
                const recsResponse = await fetch('/api/v2/dashboard/analytics/recommendations');
                const recsData = await recsResponse.json();
                updateRecommendationsChart(recsData);
                
                // Cargar analytics de debilidades
                const weaknessResponse = await fetch('/api/v2/dashboard/analytics/weaknesses');
                const weaknessData = await weaknessResponse.json();
                updateWeaknessAnalysis(weaknessData);
                
            } catch (error) {
                console.error('Error cargando dashboard:', error);
                showError('Error cargando datos del dashboard');
            }
        }
        
        function updateSystemStatus(statusData) {
            const container = document.getElementById('system-status');
            const statusClass = statusData.overall_health === 'excellent' ? 'status-healthy' : 
                               statusData.overall_health === 'good' ? 'status-healthy' :
                               statusData.overall_health === 'fair' ? 'status-warning' : 'status-critical';
            
            container.innerHTML = `
                <div class="metric">
                    <span>Estado General</span>
                    <span class="metric-value ${statusClass}">${statusData.overall_health.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span>Puntuación</span>
                    <span class="metric-value">${(statusData.overall_score * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Embeddings</span>
                    <span class="metric-value status-healthy">✓</span>
                </div>
                <div class="metric">
                    <span>Recomendaciones</span>
                    <span class="metric-value status-healthy">✓</span>
                </div>
                <div class="metric">
                    <span>Análisis Debilidades</span>
                    <span class="metric-value status-healthy">✓</span>
                </div>
            `;
        }
        
        function updateKeyMetrics(metricsData) {
            const container = document.getElementById('key-metrics');
            container.innerHTML = `
                <div class="metric">
                    <span>Estudiantes</span>
                    <span class="metric-value">${metricsData.total_students.toLocaleString()}</span>
                </div>
                <div class="metric">
                    <span>Videos</span>
                    <span class="metric-value">${metricsData.total_videos.toLocaleString()}</span>
                </div>
                <div class="metric">
                    <span>Recomendaciones</span>
                    <span class="metric-value">${metricsData.total_recommendations.toLocaleString()}</span>
                </div>
                <div class="metric">
                    <span>Precisión Sistema</span>
                    <span class="metric-value">${(metricsData.system_accuracy * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Cobertura</span>
                    <span class="metric-value">${metricsData.coverage_percentage.toFixed(1)}%</span>
                </div>
            `;
        }
        
        function updateCriticalAlerts(alertsData) {
            const container = document.getElementById('critical-alerts');
            container.innerHTML = `
                <div class="metric">
                    <span>Estudiantes Críticos</span>
                    <span class="metric-value status-critical">${alertsData.total_critical_students}</span>
                </div>
                <div class="metric">
                    <span>Temas Problemáticos</span>
                    <span class="metric-value">${alertsData.problematic_topics.length}</span>
                </div>
                <div style="margin-top: 1rem;">
                    <strong>Top Temas Problemáticos:</strong>
                    ${alertsData.problematic_topics.slice(0, 3).map(topic => 
                        `<div style="margin: 0.5rem 0; font-size: 0.9rem;">
                            • ${topic.subject_name}: ${topic.topic_name} (${topic.affected_students} estudiantes)
                        </div>`
                    ).join('')}
                </div>
            `;
        }
        
        function updatePerformanceChart(performanceData) {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            const timeLabels = performanceData.time_series.map(point => 
                new Date(point.timestamp).toLocaleDateString()
            );
            
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [
                        {
                            label: 'Requests API',
                            data: performanceData.time_series.map(point => point.api_requests),
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Recomendaciones',
                            data: performanceData.time_series.map(point => point.recommendations_generated),
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        function updateRecommendationsChart(recsData) {
            const ctx = document.getElementById('recommendations-chart').getContext('2d');
            
            if (recommendationsChart) {
                recommendationsChart.destroy();
            }
            
            const typeData = recsData.distributions.by_type;
            
            recommendationsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: typeData.map(item => item.type),
                    datasets: [{
                        data: typeData.map(item => item.count),
                        backgroundColor: [
                            '#667eea',
                            '#28a745',
                            '#ffc107',
                            '#dc3545',
                            '#17a2b8'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        function updateWeaknessAnalysis(weaknessData) {
            const container = document.getElementById('weaknesses-analysis');
            container.innerHTML = `
                <div class="metric">
                    <span>Estudiantes con Debilidades</span>
                    <span class="metric-value">${weaknessData.overview.total_students_with_weaknesses}</span>
                </div>
                <div class="metric">
                    <span>Debilidades Detectadas</span>
                    <span class="metric-value">${weaknessData.overview.total_weaknesses_detected}</span>
                </div>
                <div class="metric">
                    <span>Alertas Críticas</span>
                    <span class="metric-value status-critical">${weaknessData.overview.critical_alerts_active}</span>
                </div>
                <div class="metric">
                    <span>Prioridad Promedio</span>
                    <span class="metric-value">${weaknessData.overview.avg_intervention_priority}</span>
                </div>
                <div style="margin-top: 1rem;">
                    <strong>Distribución por Severidad:</strong>
                    ${weaknessData.severity_analysis.map(item => 
                        `<div style="margin: 0.3rem 0; font-size: 0.9rem;">
                            • ${item.severity}: ${item.count} casos (${item.unique_students} estudiantes)
                        </div>`
                    ).join('')}
                </div>
            `;
        }
        
        function refreshDashboard() {
            document.querySelectorAll('.loading').forEach(el => {
                el.textContent = 'Actualizando...';
            });
            loadDashboardData();
        }
        
        function showError(message) {
            document.querySelectorAll('.loading').forEach(el => {
                el.innerHTML = `<span style="color: #dc3545;">❌ ${message}</span>`;
            });
        }
        
        // Cargar dashboard al inicio
        document.addEventListener('DOMContentLoaded', loadDashboardData);
        
        // Auto-refresh cada 5 minutos
        setInterval(loadDashboardData, 5 * 60 * 1000);
    </script>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating HTML dashboard: {str(e)}")

# =============================================================================
# ENDPOINTS DE EXPORTACIÓN
# =============================================================================

@router.get("/export/metrics")
async def export_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    format: str = Query("json", description="Formato de exportación (json, csv)")
):
    """
    Exporta métricas del sistema en formato especificado
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Obtener todas las métricas
        overview_data = await get_dashboard_overview(db, current_user)
        performance_data = await get_performance_analytics(db, current_user)
        recommendations_data = await get_recommendations_analytics(db, current_user)
        weaknesses_data = await get_weaknesses_analytics(db, current_user)
        
        # Compilar datos para exportación
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'overview': overview_data,
            'performance': performance_data,
            'recommendations': recommendations_data,
            'weaknesses': weaknesses_data
        }
        
        if format.lower() == 'csv':
            # En implementación real se convertiría a CSV
            return JSONResponse(content={
                'message': 'CSV export not implemented yet',
                'data': export_data
            })
        else:
            return JSONResponse(content=export_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")

# =============================================================================
# CONFIGURACIÓN DEL ROUTER
# =============================================================================

@router.on_event("startup")
async def startup_dashboard():
    """Inicialización del dashboard"""
    print("Recommendations Dashboard initialized")

@router.on_event("shutdown") 
async def shutdown_dashboard():
    """Limpieza del dashboard"""
    print("Recommendations Dashboard shutdown")