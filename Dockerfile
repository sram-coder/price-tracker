FROM python:3.12-slim

LABEL authors="Sharanya Ram"

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /usr/app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser interactive_chart.py .

USER appuser

EXPOSE 5000
ENTRYPOINT ["python", "interactive_chart.py"]