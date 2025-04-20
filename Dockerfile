# Use official slim Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd gcc libpq-dev curl git supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Copy Google Cloud credentials (make sure it's ignored in .gitignore)
COPY config/directed-bongo-444307-p7-7dc58168bece.json /app/config/directed-bongo-444307-p7-7dc58168bece.json

# Copy supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose Django and Daphne ports
EXPOSE 8000
EXPOSE 8001

# Run migrations, collect static, then run supervisord
CMD bash -c "mkdir -p /app/staticfiles && \
            python manage.py makemigrations && \
             python manage.py migrate && \
             python manage.py collectstatic --noinput && \
             /usr/bin/supervisord"


