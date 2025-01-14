# Real Estate Analysis API

A robust web crawler built with Selenium to extract property listings from Bayut.com and provide analysis through a FastAPI-based API.

## Features

- Extracts detailed property information including:
  - Basic property details (ID, type, location)
  - Price and specifications
  - Geographic coordinates
  - Agent information
  - Amenities and features
  - TruCheck verification status
- Supports incremental crawling
- Async processing with Celery
- Data persistence with SQLAlchemy
- Provides analysis endpoints via FastAPI

## Prerequisites

- Python 3.8+
- Chromium Based Browser
- RabbitMQ (for Celery)
- PostgreSQL

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/KILID-test.git
cd KILID-test
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# for Linux/Mac
source .venv/bin/activate  
# for Windows
.\venv\Scripts\activate.ps1  # pwsh
.\venv\Scripts\activate.bat  # cmd
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure database:
```bash
docker-compose up -d
```

## Usage

1. Start RabbitMQ server:
```bash
rabbitmq-server
```

2. Start Celery worker:
```bash
celery -A src.processor.celery_tasks worker --loglevel=info
```

3. Run the scraper:
```bash
python -m src.crawler.realestate_crawler.spiders.bayut
```

4. Start the FastAPI server:
```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

## Project Structure

```
KILID-test/
├── src/
│   ├── api/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── middleware/
│   │   │   └── error_handler.py
│   │   └── routers/
│   │       └── analysis.py
│   ├── crawler/
│   │   └── bayut.py
│   ├── models/
│   │   └── property.py
│   └── processor/
│       └── celery_tasks.py
├── requirements.txt
└── README.md
```

## Configuration

The scraper can be configured through the following settings in `bayut.py`:

- `CONCURRENT_REQUESTS`: Number of concurrent requests
- `DOWNLOAD_DELAY`: Delay between requests
- `COOKIES_ENABLED`: Cookie handling

## Data Model

The Property model includes:
- Basic property information
- Location details
- Specifications
- Agent information
- Amenities and features
- Timestamps and metadata

## API Endpoints

### Health Check

- **GET /**: Welcome message
- **GET /health**: Health check

### Analysis Endpoints

- **GET /analysis/region-listings**: Count listings for each region and TruCheck listings
- **GET /analysis/avg-price**: Calculate average price for each region and overall
- **GET /analysis/max_min_price**: Calculate maximum and minimum price for each region and overall
