FROM python:3-alpine

WORKDIR /usr/src/app

# psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "bosko.wsgi", "--bind", "0.0.0.0:8000"]
