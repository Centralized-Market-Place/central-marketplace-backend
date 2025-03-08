# Central Marketplace Backend

This is the backend service for the **Central Marketplace** project, built with [FastAPI](https://fastapi.tiangolo.com/).

## Installation

### Prerequisites
- Python 3.12+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/)

### Setup and Run Locally

#### 1. Clone the repository:
```sh
git clone https://github.com/your-username/central-marketplace.git
cd central-marketplace
```

#### 2. Create a virtual environment and install dependencies:
```sh
python -m venv .venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
poetry install
```

#### 3. Run the FastAPI server:
```sh
uvicorn main_run:app --host 0.0.0.0 --port 8443 --reload 
```

### Running with Docker
If you prefer to run the backend in a container:

#### 1. Build and start the service:
```sh
docker compose up
```

#### 2. Stop the service:
```sh
docker compose down
```

## API Documentation
FastAPI automatically generates interactive API docs:
- **Swagger UI**: [http://localhost:8443/api/v1/docs](http://localhost:8443/api/v1/docs)
- **ReDoc**: [http://localhost:8443/api/v1/redoc](http://localhost:8443/api/v1/redoc)
