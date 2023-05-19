FROM python:3.11-alpine
LABEL maintainer="hunter@readpnw.dev"

WORKDIR /code

COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY ddns.py .

CMD ["python3", "ddns.py"]