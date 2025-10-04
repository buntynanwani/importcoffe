# Backend (Django)

This folder contains the Django backend for the ImportCoffe project.

Quick start (local development)

1. Create and activate a Python virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r .\Backend\reqs.txt
```

3. (Optional) Create a `.env` file at the project root `c:\importcoffe\.env` with environment variables, e.g.:

```text
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_ENGINE=postgresql
POSTGRES_DB=importcoffe
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_HOST=localhost
POSTGRES_PORT=5432
DJANGO_SECRET_KEY=your-secret-key
```

If `.env` is present, `configs.settings` will load it automatically (requires `python-dotenv`).

4. Apply migrations and start development server:

```powershell
python .\Backend\code\manage.py migrate
python .\Backend\code\manage.py runserver
```

5. Streamlit app is at project root. To run the UI:

```powershell
python -m streamlit run .\main.py
```

Notes
- For Docker usage, set the environment variables expected by `docker-compose.yaml`.
- Secrets should never be committed for production. Use real secret management for deployments.
