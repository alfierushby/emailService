From python:3.9.21-alpine3.21
WORKDIR /app
COPY  requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app
EXPOSE 8000
ENV P3_QUEUE_URL=""
ENV AWS_REGION=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
ENV SES_SENDER_EMAIL=""
ENV SES_RECIPIENT_EMAIL=""
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-c","gunicorn_config.py","app:create_app()"]
