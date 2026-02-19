# Dockerfile (exact filename: Dockerfile)
FROM python:3.11-slim

# set workdir
WORKDIR /app

# system deps for psycopg2 and building some packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# copy project files
COPY . /app/

# expose port
EXPOSE 8000

# create env var to prevent python from writing pyc's and enable stdout flush
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# collect static (only if you have staticfiles configured)
# run migrations and start server via gunicorn in production; for dev you can override docker-compose command
CMD ["gunicorn", "library.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
