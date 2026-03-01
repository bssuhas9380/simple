FROM python:3.11-slim
WORKDIR /app
COPY . /app/
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt 2>&1; fi
RUN if [ -f pyproject.toml ]; then pip install --no-cache-dir . 2>&1 || true; fi
RUN if [ -f setup.py ]; then pip install --no-cache-dir . 2>&1 || true; fi
CMD ["python", "009b824a0658455c8717f99ff75bf4c5_task_queue.py"]
