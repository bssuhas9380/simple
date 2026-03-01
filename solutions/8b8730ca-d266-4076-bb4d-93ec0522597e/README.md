# Task Queue Service

A production-ready async task queue REST API built with Flask.

## Features
- Create, read, update, delete tasks
- Priority levels (low, medium, high)
- Status tracking (pending, running, completed, failed, cancelled)
- Health check endpoint
- Input validation
- Structured logging
- Application factory pattern

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

The server starts on port 5000.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/v1/tasks | Create task |
| GET | /api/v1/tasks | List tasks |
| GET | /api/v1/tasks/:id | Get task |
| PUT | /api/v1/tasks/:id | Update task |
| DELETE | /api/v1/tasks/:id | Delete task |

## Example

```bash
# Create a task
curl -X POST http://localhost:5000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "process_data", "priority": "high"}'

# List tasks
curl http://localhost:5000/api/v1/tasks
```

## License
MIT
