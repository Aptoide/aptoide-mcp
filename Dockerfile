FROM python:3.12-slim

ARG USER_ID=1001
ENV PORT=8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY --chown=${USER_ID}:0 --chmod=0775 . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

USER ${USER_ID}

EXPOSE ${PORT}

ENTRYPOINT ["python", "server.py"]