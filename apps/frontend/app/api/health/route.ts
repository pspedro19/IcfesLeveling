import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Verificar que el frontend esté funcionando
    const healthStatus = {
      status: 'healthy',
      service: 'frontend',
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'development',
      port: process.env.PORT || '4001',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.version
    }

    return NextResponse.json(healthStatus, { status: 200 })
  } catch (error) {
    return NextResponse.json(
      { 
        status: 'unhealthy', 
        service: 'frontend',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      }, 
      { status: 500 }
    )
  }
}


