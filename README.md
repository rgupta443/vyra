# Vyra - Instagram Content Automation

AI-powered Instagram content generation platform with face identity consistency. Upload your face once and generate brand-safe, Instagram-ready content with captions, hashtags, and location suggestions.

## 🌟 Features

- **Face Identity Consistency**: Upload once, maintain identity across all generations (≥0.95 identity strength)
- **Preset-Based Generation**: Luxury, Lifestyle, and Beauty presets for brand-safe content
- **Instagram-Ready Formats**: 9:16 Reels, 4:5 Feed, 1:1 Square with 4K resolution
- **Complete Content Package**: Images with AI-generated captions, hashtags, and location suggestions
- **Subscription Management**: Freemium model with Stripe integration
- **Queue-Based Processing**: Reliable background job processing with Redis Queue (RQ)
- **Real-Time Updates**: WebSocket support for generation status tracking

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Manual Setup](#manual-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required
- **Python 3.9+** (3.11 recommended)
- **Node.js 18+** and npm
- **PostgreSQL 15+**
- **Redis 7+**

### Optional (for Docker setup)
- **Docker** and **Docker Compose**

### External Services
- **OpenAI API Key** (for caption and hashtag generation)
- **Nano Banana API Key** (Google Gemini 2.5 Flash Image for image generation)
- **Stripe Account** (for payment processing)

## 🚀 Quick Start (Docker)

The fastest way to get started is using Docker Compose, which sets up all services automatically.

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/rgupta443/vyra.git
cd vyra

# Copy environment file
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and add your API keys:

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-api-key
NANO_BANANA_API_KEY=your-nano-banana-api-key

# Stripe Keys (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Generate a secure secret key
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 3. Start All Services

```bash
# Start PostgreSQL, Redis, API, and Worker
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Initialize default presets
docker-compose exec api python scripts/init_presets.py
```

### 5. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy frontend environment file
cp .env.local.example .env.local

# Edit .env.local with your configuration
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXTAUTH_URL=http://localhost:3000
# NEXTAUTH_SECRET=your-nextauth-secret

# Start development server
npm run dev
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

### 7. Verify Setup

```bash
# Check backend health
curl http://localhost:8000/health

# Check API status
curl http://localhost:8000/api/status

# View logs
docker-compose logs -f api
docker-compose logs -f worker
```

## 🛠️ Manual Setup

If you prefer not to use Docker, follow these steps:

### 1. Install System Dependencies

**macOS:**
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-15 redis-server
sudo systemctl start postgresql
sudo systemctl start redis
```

### 2. Setup Database

```bash
# Create database and user
psql postgres
CREATE DATABASE instagram_automation;
CREATE USER instagram_user WITH PASSWORD 'instagram_password';
GRANT ALL PRIVILEGES ON DATABASE instagram_automation TO instagram_user;
\q
```

### 3. Setup Python Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Note: If you encounter bcrypt issues, install bcrypt 4.x
pip install 'bcrypt<5.0.0'
```

### 4. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your configuration
```

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Initialize presets
python scripts/init_presets.py

# Verify setup
python scripts/check_setup.py
```

### 6. Start Backend Services

Open 3 terminal windows:

**Terminal 1 - API Server:**
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Background Worker:**
```bash
source .venv/bin/activate
python -m app.worker.worker --type all
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## ⚙️ Configuration

### Backend Environment Variables (.env)

```bash
# Environment
ENVIRONMENT=development  # development, staging, production

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=instagram_user
POSTGRES_PASSWORD=instagram_password
POSTGRES_DB=instagram_automation
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password

# External APIs
OPENAI_API_KEY=sk-your-openai-api-key
NANO_BANANA_API_KEY=your-nano-banana-api-key

# Stripe
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# File Storage
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend Environment Variables (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret-here

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Stripe (for frontend)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
```

### Obtaining API Keys

**OpenAI:**
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Add credits to your account

**Nano Banana (Google Gemini):**
1. Visit https://aistudio.google.com/app/apikey
2. Create a new API key
3. Enable Gemini 2.5 Flash Image API

**Stripe:**
1. Visit https://dashboard.stripe.com/test/apikeys
2. Copy your test keys
3. For webhooks: https://dashboard.stripe.com/test/webhooks

## 🏃 Running the Application

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart api
docker-compose restart worker

# Rebuild after code changes
docker-compose up -d --build
```

### Manual Execution

**Start Backend:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
python run.py
```

**Start Worker:**
```bash
# In a separate terminal
source .venv/bin/activate
python -m app.worker.worker --type all

# Or start specific worker types
python -m app.worker.worker --type generation
python -m app.worker.worker --type processing
```

**Start Frontend:**
```bash
cd frontend
npm run dev

# Or for production build
npm run build
npm start
```

## 🧪 Testing

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_health_endpoint
```

### Test Categories

```bash
# Unit tests
pytest tests/test_presets.py
pytest tests/test_payments.py
pytest tests/test_queue.py

# Integration tests
pytest tests/test_nano_banana.py
pytest tests/test_e2e_integration.py

# Run tests in parallel
pytest -n auto
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

## 📁 Project Structure

```
vyra/
├── app/                          # Backend application
│   ├── api/v1/                   # API endpoints
│   │   ├── endpoints/            # Route handlers
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── faces.py          # Face upload/management
│   │   │   ├── generate.py       # Content generation
│   │   │   ├── payments.py       # Stripe integration
│   │   │   ├── plans.py          # Subscription plans
│   │   │   └── queue.py          # Job queue management
│   │   └── api.py                # API router
│   ├── core/                     # Core functionality
│   │   ├── config.py             # Configuration management
│   │   ├── database.py           # Database connection
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   ├── queue.py              # Queue management
│   │   ├── redis.py              # Redis connection
│   │   └── security.py           # Authentication/security
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py               # User model
│   │   ├── face.py               # Face model
│   │   ├── generation.py         # Generation model
│   │   ├── preset.py             # Preset model
│   │   └── analytics.py          # Analytics models
│   ├── schemas/                  # Pydantic schemas
│   │   ├── auth.py               # Auth schemas
│   │   ├── face.py               # Face schemas
│   │   ├── generation.py         # Generation schemas
│   │   └── payment.py            # Payment schemas
│   ├── services/                 # Business logic
│   │   ├── user_service.py       # User management
│   │   ├── face_service.py       # Face processing
│   │   ├── generation_service.py # Content generation
│   │   ├── nano_banana_service.py # Image generation API
│   │   ├── caption_service.py    # Caption generation
│   │   ├── hashtag_service.py    # Hashtag generation
│   │   ├── location_service.py   # Location suggestions
│   │   ├── payment_service.py    # Stripe integration
│   │   ├── preset_service.py     # Preset management
│   │   ├── analytics_service.py  # Analytics tracking
│   │   └── monitoring_service.py # System monitoring
│   ├── worker/                   # Background workers
│   │   ├── worker.py             # Worker entry point
│   │   └── tasks.py              # Job tasks
│   ├── middleware/               # FastAPI middleware
│   │   ├── error_handler.py      # Error handling
│   │   └── session_middleware.py # Session management
│   └── main.py                   # FastAPI application
├── frontend/                     # Next.js frontend
│   ├── app/                      # App Router pages
│   │   ├── auth/                 # Authentication pages
│   │   ├── dashboard/            # User dashboard
│   │   ├── generate/             # Generation interface
│   │   ├── history/              # Generation history
│   │   └── results/              # Results display
│   ├── components/               # React components
│   │   ├── auth/                 # Auth components
│   │   ├── face/                 # Face upload
│   │   └── export/               # Export buttons
│   ├── lib/                      # Utilities
│   │   ├── api.ts                # API client
│   │   └── hooks/                # React hooks
│   └── types/                    # TypeScript types
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   └── env.py                    # Alembic config
├── tests/                        # Test suite
│   ├── test_auth.py              # Auth tests
│   ├── test_presets.py           # Preset tests
│   ├── test_payments.py          # Payment tests
│   ├── test_queue.py             # Queue tests
│   ├── test_nano_banana.py       # Integration tests
│   └── test_e2e_integration.py   # E2E tests
├── scripts/                      # Utility scripts
│   ├── init_presets.py           # Initialize presets
│   └── check_setup.py            # Verify setup
├── docker-compose.yml            # Docker services
├── Dockerfile                    # Docker image
├── requirements.txt              # Python dependencies
├── alembic.ini                   # Alembic configuration
├── pytest.ini                    # Pytest configuration
└── README.md                     # This file
```

## 📚 API Documentation

### Interactive Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**Authentication:**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/google` - Google OAuth
- `GET /api/v1/auth/me` - Get current user

**Face Management:**
- `POST /api/v1/faces/upload` - Upload face image
- `GET /api/v1/faces/current` - Get current face
- `DELETE /api/v1/faces/current` - Delete face

**Content Generation:**
- `POST /api/v1/generate/image` - Generate content
- `GET /api/v1/generate/status/{job_id}` - Check status
- `GET /api/v1/generate/history` - Get history

**Payments:**
- `GET /api/v1/payments/plans` - Get available plans
- `POST /api/v1/payments/create-checkout` - Create checkout
- `POST /api/v1/payments/webhook` - Stripe webhook

**Queue Management:**
- `GET /api/v1/queue/health` - Queue health check
- `GET /api/v1/queue/stats` - Queue statistics
- `GET /api/v1/queue/job/{job_id}` - Job status

## 🔍 Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check PostgreSQL is running
docker-compose ps postgres
# Or manually: pg_isready -h localhost -p 5432

# Check credentials in .env match database
psql -U instagram_user -d instagram_automation -h localhost
```

**2. Redis Connection Error**
```bash
# Check Redis is running
docker-compose ps redis
# Or manually: redis-cli ping

# Should return: PONG
```

**3. Worker Not Processing Jobs**
```bash
# Check worker logs
docker-compose logs -f worker

# Restart worker
docker-compose restart worker

# Check Redis queue
redis-cli
> KEYS *
> LLEN rq:queue:generation
```

**4. Frontend Can't Connect to Backend**
```bash
# Check NEXT_PUBLIC_API_URL in frontend/.env.local
# Should be: http://localhost:8000

# Check CORS settings in backend .env
# Should include: http://localhost:3000
```

**5. Bcrypt/Passlib Errors**
```bash
# Install compatible bcrypt version
pip install 'bcrypt<5.0.0'
```

**6. Migration Errors**
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### Logs and Debugging

**View Logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100 api
```

**Enable Debug Mode:**
```bash
# In .env
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart api worker
```

**Database Debugging:**
```bash
# Connect to database
docker-compose exec postgres psql -U instagram_user -d instagram_automation

# Check tables
\dt

# Check users
SELECT id, email, plan_type, credits FROM users;

# Check generations
SELECT id, user_id, status, preset_type FROM generations;
```

### Performance Issues

**Slow Generation:**
- Check worker is running: `docker-compose ps worker`
- Check Redis queue: `redis-cli LLEN rq:queue:generation`
- Monitor API keys rate limits (OpenAI, Nano Banana)

**High Memory Usage:**
- Limit worker concurrency in `app/worker/worker.py`
- Increase Docker memory limits in Docker Desktop
- Monitor with: `docker stats`

## 🚢 Production Deployment

### Environment Setup

1. Set `ENVIRONMENT=production` in `.env`
2. Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
3. Use production database (not localhost)
4. Enable HTTPS
5. Set secure CORS origins
6. Use production Stripe keys

### Database

```bash
# Run migrations
alembic upgrade head

# Backup database
pg_dump -U instagram_user instagram_automation > backup.sql
```

### Security Checklist

- [ ] Change all default passwords
- [ ] Use environment-specific API keys
- [ ] Enable HTTPS/TLS
- [ ] Set secure cookie flags
- [ ] Configure rate limiting
- [ ] Enable monitoring and logging
- [ ] Set up automated backups
- [ ] Configure firewall rules

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at `/docs`