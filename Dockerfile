FROM python:3.12.3-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV TZ=America/Chicago

WORKDIR /rems

COPY ./requirements.txt .

RUN apt-get update && \
    apt-get install -y tzdata &&\
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "celery -A app.celery worker -l info & gunicorn --bind 0.0.0.0:8000 --workers 4 app.wsgi:application"]