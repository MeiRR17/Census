FROM apache/superset:latest

USER root

# מתקינים את פוסטגרס ישירות לתוך תיקיית הפייתון של סופרסט כדי לעקוף בעיות של סביבות וירטואליות
RUN pip install --target /app/pythonpath --no-cache-dir psycopg2-binary==2.9.9

COPY superset_config.py /app/pythonpath/superset_config.py

USER superset

# Run gunicorn directly with Superset
CMD ["gunicorn", "-w", "2", "--threads", "4", "-k", "gthread", "--timeout", "120", "-b", "0.0.0.0:8088", "--limit-request-line", "0", "--limit-request-field_size", "0", "superset.app:create_app()"]