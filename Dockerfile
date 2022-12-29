FROM python:3.9-slim
RUN apt update \
    && apt install -y netcat locales nano \
    && addgroup inner \
    && adduser --system --shell /bin/bash --disabled-login --home /home/appuser --ingroup inner appuser

WORKDIR /home/appuser

COPY . .

ENV TZ=Europe/Moscow \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 


RUN pip3 install -r requirements.txt

RUN chown -R appuser:inner /home/appuser
RUN chmod +x ./utils/wait-for.sh

USER appuser