# Builder #
FROM python:3-alpine as builder

# psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

WORKDIR /wheels

COPY requirements.txt ./

RUN pip install -U pip \
    && pip wheel --no-deps -r ./requirements.txt


# Final #
FROM python:3-alpine

WORKDIR /usr/src/app

# Install dependencies
RUN apk update && apk add libpq
COPY --from=builder /wheels /wheels
RUN pip install -U pip \
    && pip install --no-cache -r /wheels/requirements.txt -f /wheels \
    && rm -rf /wheels

COPY . .

EXPOSE 8000

RUN python3 manage.py collectstatic

COPY ./entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "bosko.wsgi", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]
