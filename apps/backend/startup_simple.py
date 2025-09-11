#!/usr/bin/env python
"""
Simple startup script that runs a minimal version of the backend
"""
import os
import sys

# Set Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for Docker connection
os.environ['DATABASE_URL'] = 'postgresql://gameplay:gameplay123@localhost:5433/gameplay_db'
os.environ['JWT_SECRET'] = 'your-super-secret-jwt-key-change-in-production'
os.environ['ENVIRONMENT'] = 'development'

# Start the server with minimal routes
if __name__ == "__main__":
    import uvicorn
    
    # Create a minimal app
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="ICFES Leveling API")
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add health check
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "backend"}
    
    @app.get("/")
    def root():
        return {"message": "ICFES Leveling API is running"}
    
    # Test database connection first
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        engine = create_engine(os.environ['DATABASE_URL'])
        with Session(engine) as db:
            result = db.execute(text("SELECT COUNT(*) FROM questions")).scalar()
            print(f"Database connection successful - Found {result} questions")
    except Exception as e:
        print(f"Database connection failed: {e}")
    
    # Try to import basic routes
    try:
        from app.routes import auth_simple
        app.include_router(auth_simple.router)
        print("✓ Auth routes loaded")
    except Exception as e:
        print(f"✗ Could not load auth routes: {e}")
    
    try:
        from app.routes import diagnostic_public
        app.include_router(diagnostic_public.router)
        app.include_router(diagnostic_public.router, prefix="/api/v1")
        print("✓ Diagnostic public routes loaded")
    except Exception as e:
        print(f"✗ Could not load diagnostic routes: {e}")
    
    try:
        from app.routes import dynamic_subjects
        app.include_router(dynamic_subjects.router, prefix="/api/v1")
        print("✓ Dynamic subjects routes loaded")
    except Exception as e:
        print(f"✗ Could not load subjects routes: {e}")
    
    print("\n" + "="*50)
    print("ICFES Backend Starting (Simple Mode)")
    print("="*50)
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Diagnostic API: http://localhost:8000/api/v1/diagnostic-public/diagnostic-questions/{subject_id}")
    print("="*50 + "\n")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)