FROM python:3.12-slim AS builder

RUN pip install --upgrade pip

RUN mkdir /Backend

WORKDIR /Backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

COPY reqs.txt .
RUN pip install --no-cache-dir -r reqs.txt

FROM python:3.12-slim

RUN mkdir /Backend

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder  /usr/local/bin/ /usr/local/bin/

WORKDIR /Backend

COPY . /Backend/

RUN mkdir /Backend/code/static
RUN mkdir /Backend/code/staticfiles

#RUN python3 -m django migrate --settings=Backend.code.configs.settings
#RUN python3 -m django collectstatic --settings=Backend.code.configs.settings --noinput

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

RUN chmod +x script.sh

CMD ["sh", "./script.sh"]

#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "Backend.code.configs.wsgi:application"]