'use client';

import { useDynamicSubjects } from '../../components/DynamicSubjectIcon';
import DynamicSubjectIcon from '../../components/DynamicSubjectIcon';

export default function WorkingDiagnostic() {
  const { subjects, loading, error } = useDynamicSubjects();

  const handleStartTest = (subject: any) => {
    console.log('🎯 Starting test for:', subject.name);
    alert(`🚀 ¡Iniciando diagnóstico de ${subject.name}!

📊 Preguntas: ${subject.config?.total_questions || 45}
⏱️ Tiempo: ${subject.config?.time_limit_minutes || 60} minutos

¡El sistema dinámico está funcionando correctamente!
En una aplicación completa, esto te llevaría al test real.`);
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #000000 0%, #6b46c1 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '3px solid #6b46c1',
            borderTop: '3px solid #ffffff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <h2>🔄 Cargando materias dinámicamente...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #000000 0%, #dc2626 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{ textAlign: 'center', background: 'rgba(220, 38, 38, 0.3)', padding: '32px', borderRadius: '12px' }}>
          <h2 style={{ color: '#fca5a5', marginBottom: '16px' }}>❌ Error de Conexión</h2>
          <p style={{ color: '#fed7d7' }}>{error}</p>
          <p style={{ color: '#fecaca', fontSize: '0.875rem', marginTop: '8px' }}>
            No se pudieron cargar las materias dinámicamente
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #000000 0%, #6b46c1 100%)',
      color: 'white',
      fontFamily: 'Arial, sans-serif',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ 
            fontSize: '3rem', 
            fontWeight: 'bold', 
            color: '#fbbf24',
            marginBottom: '16px',
            textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
          }}>
            🏰 Academia de Hunters ICFES
          </h1>
          <p style={{ 
            fontSize: '1.25rem', 
            color: '#c084fc',
            marginBottom: '24px'
          }}>
            Inicia tu viaje épico hacia la conquista del conocimiento
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <span style={{
              background: 'rgba(107, 70, 193, 0.3)',
              border: '1px solid #6b46c1',
              borderRadius: '20px',
              padding: '8px 16px',
              fontSize: '0.875rem',
              color: '#c084fc'
            }}>
              🏆 Sistema Adaptativo IA
            </span>
            <span style={{
              background: 'rgba(107, 70, 193, 0.3)',
              border: '1px solid #6b46c1',
              borderRadius: '20px',
              padding: '8px 16px',
              fontSize: '0.875rem',
              color: '#c084fc'
            }}>
              ⚔️ Gamificación Épica
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #6b46c1',
          borderRadius: '12px',
          padding: '32px',
          marginBottom: '32px'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <h3 style={{ 
              fontSize: '2rem', 
              fontWeight: 'bold', 
              color: '#fbbf24',
              marginBottom: '8px'
            }}>
              ⚔️ Elige tu Primera Conquista
            </h3>
            <p style={{ color: '#c084fc' }}>
              Comenzarás con un diagnóstico místico para evaluar tu poder actual
            </p>
          </div>

          {/* Subjects Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px'
          }}>
            {subjects.map((subject) => (
              <div
                key={subject.id}
                onClick={() => handleStartTest(subject)}
                style={{
                  background: 'rgba(0, 0, 0, 0.4)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(107, 70, 193, 0.5)',
                  borderRadius: '12px',
                  padding: '24px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  textAlign: 'center'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'scale(1.05)';
                  e.currentTarget.style.borderColor = '#fbbf24';
                  e.currentTarget.style.boxShadow = '0 0 20px rgba(251, 191, 36, 0.5)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.borderColor = 'rgba(107, 70, 193, 0.5)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {/* Dynamic Subject Icon */}
                <div style={{
                  width: '80px',
                  height: '80px',
                  margin: '0 auto 16px',
                  borderRadius: '50%',
                  backgroundColor: subject.display?.color_primary || subject.color || '#8B5CF6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
                }}>
                  <DynamicSubjectIcon 
                    subjectId={subject.id}
                    subjectName={subject.name}
                    size={48}
                    className="text-white"
                  />
                </div>
                
                {/* Subject Title */}
                <h3 style={{
                  fontSize: '1.25rem',
                  fontWeight: 'bold',
                  color: '#fbbf24',
                  marginBottom: '8px'
                }}>
                  {subject.name}
                </h3>
                
                {/* Subject Description */}
                <p style={{
                  color: '#c084fc',
                  marginBottom: '16px',
                  fontSize: '0.875rem'
                }}>
                  {subject.display?.description_short || subject.description || 'Conquista esta materia'}
                </p>
                
                {/* Subject Details */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                    fontSize: '0.875rem'
                  }}>
                    <span style={{ color: '#9ca3af' }}>⚔️ Combates:</span>
                    <span style={{ color: '#c084fc', fontWeight: '500' }}>
                      {subject.config?.total_questions || 45}
                    </span>
                  </div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem'
                  }}>
                    <span style={{ color: '#9ca3af' }}>⏱️ Tiempo:</span>
                    <span style={{ color: '#c084fc', fontWeight: '500' }}>
                      {subject.config?.time_limit_minutes || 60} min
                    </span>
                  </div>
                </div>
                
                {/* Start Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStartTest(subject);
                  }}
                  style={{
                    width: '100%',
                    background: 'linear-gradient(90deg, #6b46c1, #3b82f6)',
                    color: 'white',
                    fontWeight: 'bold',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'linear-gradient(90deg, #553c9a, #2563eb)';
                    e.currentTarget.style.transform = 'scale(1.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'linear-gradient(90deg, #6b46c1, #3b82f6)';
                    e.currentTarget.style.transform = 'scale(1)';
                  }}
                >
                  ⚔️ Iniciar Diagnóstico
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Success Message */}
        <div style={{
          textAlign: 'center',
          background: 'rgba(5, 150, 105, 0.2)',
          border: '1px solid #10b981',
          borderRadius: '12px',
          padding: '24px'
        }}>
          <h2 style={{
            color: '#10b981',
            fontWeight: 'bold',
            fontSize: '1.5rem',
            marginBottom: '8px'
          }}>
            ✅ ¡SISTEMA DINÁMICO DE DIAGNÓSTICO ACTIVO!
          </h2>
          <p style={{ color: '#34d399' }}>
            {subjects.length} materias cargadas dinámicamente desde la base de datos.
          </p>
          <p style={{ 
            color: '#6ee7b7', 
            fontSize: '0.875rem', 
            marginTop: '8px' 
          }}>
            🚀 Sistema inteligente con configuración dinámica y gestión de assets
          </p>
        </div>
      </div>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}