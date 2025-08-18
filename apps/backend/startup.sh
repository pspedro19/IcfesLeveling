#!/bin/bash

echo "🚀 Starting ICFES Backend Services..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
while ! pg_isready -h postgres -p 5432 -U gameplay > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready!"

# Initialize database with all data
echo "📊 Initializing database with ICFES data..."
python /app/app/scripts/populate_subjects_direct.py
python /app/app/scripts/initialize_all_data.py

# Create test users
echo "👤 Creating test users..."
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import uuid

try:
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter_by(username='admin').first()
    if not admin:
        admin_user = User(
            id=uuid.uuid4(),
            username='admin',
            email='admin@test.com',
            hashed_password=get_password_hash('secret'),
            level=50,
            experience=10000,
            rank='S',
            hp=200,
            mp=150,
            power=50,
            wisdom=50,
            speed=50,
            orbs=1000,
            crystals=500,
            premium_plan='premium',
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print('✅ Admin user created')
    else:
        print('ℹ️ Admin user already exists')
        
    db.close()
except Exception as e:
    print(f'⚠️ Could not create users: {e}')
"

echo "🎯 Starting FastAPI application..."
# Start the FastAPI application
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload