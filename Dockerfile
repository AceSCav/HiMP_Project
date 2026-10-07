FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_DEBUG=false
WORKDIR /app
COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt
COPY web/ ./
RUN DJANGO_DEBUG=true python manage.py collectstatic --noinput \
    && groupadd --gid 10001 himp \
    && useradd --uid 10001 --gid himp --no-create-home himp \
    && mkdir -p private_media && chown himp:himp private_media
USER himp
EXPOSE 8000
CMD ["gunicorn", "himp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-"]
