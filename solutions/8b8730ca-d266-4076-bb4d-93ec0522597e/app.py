"""
Task Queue Service - A production-ready async task queue built with Flask.

This service provides a REST API for creating, managing, and monitoring
asynchronous tasks. It supports task priorities, status tracking, and
result retrieval.

Author: Developer
Version: 1.0.0
License: MIT
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from flask import Flask, request, jsonify
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app(config: Optional[dict] = None) -> Flask:
    """Application factory pattern for creating the Flask app."""
    app = Flask(__name__)

    if config:
        app.config.update(config)

    # In-memory task store (would be Redis/DB in production)
    tasks: dict = {}

    def validate_json(f):
        """Decorator to validate JSON request body."""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 415
            return f(*args, **kwargs)
        return decorated

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            "status": "healthy",
            "service": "task-queue",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tasks_count": len(tasks),
        })

    @app.route("/api/v1/tasks", methods=["POST"])
    @validate_json
    def create_task():
        """
        Create a new task.

        Request body:
            name (str): Task name (required)
            payload (dict): Task data (optional)
            priority (str): low, medium, high (default: medium)

        Returns:
            201: Task created successfully
            400: Invalid request
        """
        data = request.get_json()

        if not data.get("name"):
            return jsonify({"error": "Task name is required"}), 400

        priority = data.get("priority", "medium")
        if priority not in ("low", "medium", "high"):
            return jsonify({"error": "Priority must be low, medium, or high"}), 400

        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "name": data["name"],
            "payload": data.get("payload", {}),
            "priority": priority,
            "status": "pending",
            "result": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        tasks[task_id] = task
        logger.info("Task created: %s (%s)", task["name"], task_id)
        return jsonify(task), 201

    @app.route("/api/v1/tasks", methods=["GET"])
    def list_tasks():
        """
        List all tasks with optional filtering.

        Query params:
            status (str): Filter by status
            priority (str): Filter by priority
            limit (int): Max results (default: 50)
        """
        status_filter = request.args.get("status")
        priority_filter = request.args.get("priority")
        limit = min(int(request.args.get("limit", 50)), 100)

        result = list(tasks.values())

        if status_filter:
            result = [t for t in result if t["status"] == status_filter]
        if priority_filter:
            result = [t for t in result if t["priority"] == priority_filter]

        result.sort(key=lambda t: t["created_at"], reverse=True)
        return jsonify({"tasks": result[:limit], "total": len(result)})

    @app.route("/api/v1/tasks/<task_id>", methods=["GET"])
    def get_task(task_id: str):
        """Get a specific task by ID."""
        task = tasks.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task)

    @app.route("/api/v1/tasks/<task_id>", methods=["PUT"])
    @validate_json
    def update_task(task_id: str):
        """Update task status and result."""
        task = tasks.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        data = request.get_json()
        if "status" in data:
            valid_statuses = ("pending", "running", "completed", "failed", "cancelled")
            if data["status"] not in valid_statuses:
                return jsonify({"error": f"Status must be one of: {valid_statuses}"}), 400
            task["status"] = data["status"]

        if "result" in data:
            task["result"] = data["result"]

        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("Task updated: %s -> %s", task_id, task["status"])
        return jsonify(task)

    @app.route("/api/v1/tasks/<task_id>", methods=["DELETE"])
    def delete_task(task_id: str):
        """Delete a task."""
        if task_id not in tasks:
            return jsonify({"error": "Task not found"}), 404
        del tasks[task_id]
        logger.info("Task deleted: %s", task_id)
        return jsonify({"message": "Task deleted"}), 200

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal server error: %s", error)
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
