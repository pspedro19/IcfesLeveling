# 🎮 ICFES Leveling - Educational Gamification Platform

<div align="center">
  
![ICFES Leveling](https://img.shields.io/badge/Version-1.0.0-brightgreen)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![License](https://img.shields.io/badge/License-MIT-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Tests](https://img.shields.io/badge/Tests-96%25%20Passing-brightgreen)

**Transform your ICFES preparation into an epic RPG adventure inspired by Solo Leveling**

[Demo](http://localhost:4001) • [API Docs](http://localhost:4000/docs) • [Report Issue](https://github.com/icfes-leveling/issues)

</div>

---

## 🚀 Overview

ICFES Leveling is a **Coursera-grade educational platform** that gamifies ICFES exam preparation using Solo Leveling themes. Students become "Hunters" who level up from E-rank to SSS-rank by completing personalized study plans, watching educational videos, and defeating academic challenges.

### ✨ Key Features

- 🎯 **Intelligent Diagnostic Tests** - AI-powered weakness detection
- 📚 **Personalized Study Plans** - Adaptive learning paths based on performance
- 🎥 **270+ YouTube Videos** - Direct iframe integration (no API required)
- ⚔️ **Gamification System** - XP, ranks, achievements, and boss battles
- 📊 **Real-time Analytics** - Track progress with ClickHouse
- 🏆 **Leaderboards** - Compete globally, weekly, and monthly
- 💬 **Guild System** - Collaborate with other students
- 📱 **Responsive Design** - Works on all devices

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 14)                │
│                    TypeScript • Tailwind CSS • Framer        │
└─────────────┬───────────────────────────────────┬───────────┘
              │                                   │
       ┌──────▼──────┐                    ┌──────▼──────┐
       │   Nginx     │                    │  WebSocket  │
       │   Proxy     │                    │   Server    │
       └──────┬──────┘                    └──────┬──────┘
              │                                   │
┌─────────────▼───────────────────────────────────▼───────────┐
│                      Backend API (FastAPI)                   │
│              Python 3.11 • SQLAlchemy • Pydantic            │
└──────┬──────────┬──────────┬──────────┬──────────┬─────────┘
       │          │          │          │          │
   ┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
   │Postgres│ │ Redis │ │AI Svc │ │Click  │ │Docker │
   │  DB    │ │ Cache │ │OpenAI │ │House  │ │Engine │
   └────────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/icfes-leveling.git
cd icfes-leveling
```

2. **Set up environment variables**
```bash
cp .env.example .env.development
# Edit .env.development with your configuration
```

3. **Start with Docker**
```bash
docker-compose up -d
```

4. **Access the platform**
- Frontend: http://localhost:4001
- Backend API: http://localhost:4000
- API Documentation: http://localhost:4000/docs

### Default Credentials
- **Admin**: admin / secret
- **Test User**: test / secret

## 📊 Data & Content

### ICFES Question Bank
- **2000+ Questions** across all ICFES subjects
- **270+ YouTube Videos** with direct iframe embedding
- **Adaptive Learning** based on performance
- **Solo Leveling Gamification** from E-rank to SSS-rank

### Study Plan Features
- **Coursera-Grade UI/UX** with modern, interactive design
- **Personalized Learning Paths** based on diagnostic results
- **XP & Achievement System** for motivation
- **Boss Battles** at the end of each unit
- **Real-time Progress Tracking** with analytics

## 🧪 Testing

### End-to-End Flow
1. User Registration → 2. Diagnostic Test → 3. Rank Assignment → 4. Study Plan Generation → 5. Video Learning → 6. Progress Tracking

### API Testing
```bash
# Test authentication
curl -X POST http://localhost:4000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"secret"}'

# Test diagnostic endpoint
curl http://localhost:4000/diagnostic/start

# Test study plan generation
curl http://localhost:4000/study-plans/generate
```

## 🚀 Production Deployment

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `JWT_SECRET`: JWT secret key
- `ENVIRONMENT`: production/development

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  
**Built with ❤️ for ICFES preparation**

[Report Bug](https://github.com/icfes-leveling/issues) • [Request Feature](https://github.com/icfes-leveling/issues)

</div>

 