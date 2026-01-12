# Instagram Content Automation

AI-powered Instagram content generation with face identity consistency.

## Features

- **Face Identity Consistency**: Upload once, maintain identity across all generations
- **Preset-Based Generation**: Luxury, Lifestyle, and Beauty presets for brand-safe content
- **Instagram-Ready Formats**: 9:16 Reels, 4:5 Feed, 1:1 Square with 4K resolution
- **Complete Content Package**: Images with captions, hashtags, and location suggestions
- **Subscription Management**: Freemium model with Stripe integration

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd instagram-content-automation
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Run database migrations:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

4. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database:**
   ```bash
   # Start PostgreSQL and Redis
   alembic upgrade head
   ```

3. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Start background workers:**
   ```bash
   rq worker generation processing
   ```

## Project Structure

```
app/
├── api/v1/           # API endpoints
├── core/             # Core configuration and utilities
├── models/           # Database models
└── main.py           # FastAPI application entry point

alembic/              # Database migrations
docker-compose.yml    # Development environment
requirements.txt      # Python dependencies
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Environment Variables

Copy `.env.example` to `.env` and configure:

- **Database**: PostgreSQL connection settings
- **Redis**: Job queue configuration
- **APIs**: OpenAI, Nano Banana, Stripe keys
- **Security**: JWT secret key
- **Storage**: File upload configuration

## Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## License

[Add your license here]