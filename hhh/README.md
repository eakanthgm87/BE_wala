FarmLink Exchange - full project scaffold
----------------------------------------
This project is a full-stack Django + DRF application scaffold for FarmLink Exchange.

How to run locally (simple):
1. python -m venv venv
2. source venv/bin/activate
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py createsuperuser
6. python manage.py runserver

Notes:
- Settings default to sqlite. To use PostgreSQL set USE_POSTGRES=True and configure env vars.
- OpenLayers is used in templates for mapping.
- This scaffold includes API endpoints under /api/
nnn
