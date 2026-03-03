# Template Creation - Django Document Processor

This repository contains a complete Django project with the `document_processor` app.

## What is included

- `manage.py`
- `project_config/` Django project package (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`)
- `document_processor/` app package:
  - models, views, forms, permissions, urls, admin
  - services (`textract_service`, `extraction_engine`, `document_builder`)
  - templates for user and admin workflows
  - migrations package

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## App URL

- Dashboard: `http://127.0.0.1:8000/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Notes

- Default database is SQLite for local development.
- AWS Textract credentials/region should be configured in your environment for processing features.

## Recommended setup order

1. Login as admin and open `/admin-portal/`.
2. Configure **Template Types**.
3. Upload active **Word Templates** per type.
4. Configure and enable **Extraction Rules**.
5. Assign user roles from **User Management**.
6. Users then upload and process PDFs from `/upload/`.
