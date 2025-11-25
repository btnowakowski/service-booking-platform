# Accommodations – Django Booking System

**Accommodations** is a small, production‑ready booking system built with Django.  
The app lets users browse services, book available time slots in a calendar view, and track the status of their reservations.  
Admins get a dedicated panel where they can manage services, slots, and approve or reject bookings.


This repository contains the Django project along with a Dockerfile for building the application image, but does not include full server infrastructure (no docker-compose, nginx config, certificates, deployment scripts).
The goal is to keep the project clean, easy to read, and simple to run locally.

---

## Main Features

### For users
- List of services with name, description and price
- Service detail with interactive calendar (FullCalendar) showing available slots
- Booking by clicking a free time slot
- User account registration, login and logout
- “My reservations” panel:
  - list of user’s own reservations
  - filtering by status and service
  - clear, Polish status labels:
    - `Oczekująca` (pending)
    - `Zatwierdzona` (approved)
    - `Anulowana` (cancelled)
    - `Odrzucona` (rejected)

### For admins (custom admin panel)
Separate app admin panel (different from Django’s built‑in `/admin/`) available at:

- `/admin-panel/`

Features:
- Dashboard with basic stats:
  - total reservations
  - pending / approved / cancelled / rejected counts
- Quick actions:
  - approve / reject reservations directly from lists
- Service management:
  - add / edit / delete services
- Time slot management:
  - add / edit / delete time slots
  - toggle slot activity (is_active)
- Cleaner UI integrated with the main dark theme
  <img width="1020" height="857" alt="image" src="https://github.com/user-attachments/assets/a8ebc129-d447-438f-894a-dd15a1878cca" />


### UX and UI
- Global dark theme with custom CSS (`booking/static/booking/style.css`)
- Responsive layout using Bootstrap 5
- Consistent navigation:
  - services
  - my reservations
  - admin panel (only for admin group)
- Calendar view:
  - week/day views
  - Polish locale
  - hidden / muted calendar when no free slots are available
  - helper messages for users when there are no terms

---

## Tech Stack

- **Backend**: Django 5
- **Database**: PostgreSQL (in production), SQLite possible locally
- **Frontend**:
  - Django templates
  - Bootstrap 5
  - FullCalendar for time slots
- **Auth**:
  - Django auth
  - custom registration view & form
  - login view using `CustomAuthForm`
- **Other**:
  - `.env` support with `python-dotenv`
  - separated “app admin” vs Django admin

---

## Local Development Setup

Below is a straightforward way to run the project locally for development.

### 1. Clone the repository

```bash
git clone https://github.com/btnowakowski/mvc_projekt_semestralny.git
cd mvc_projekt_semestralny
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows (PowerShell / CMD):**
```bash
.venv\Scriptsctivate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment (optional but recommended)

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-dev-secret-key
DJANGO_DEBUG=1
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost
```

For local development you can:
- either configure PostgreSQL and fill DB_* variables,
- or temporarily switch the `DATABASES` setting back to SQLite.

```env
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }
```

### 5. Enabling Admin Panel
The Django admin panel is disabled by default in production.

To enable it locally, open:

```
mvc_projekt_semestralny/urls.py
```

and uncomment:

```python
path("admin/", admin.site.urls),
```

Admin interface will be available at:
http://127.0.0.1:8000/admin/

### 6. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser (optional, useful for Django `/admin/`)

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

The app will be available at:

- Main app: http://127.0.0.1:8000/  
- Django admin: http://127.0.0.1:8000/admin/  
- App admin panel: http://127.0.0.1:8000/admin-panel/  

---

## Groups and Permissions

The app uses a simple group‑based check for the custom admin panel:

- Add a group named **`Admin`** in Django admin (`/admin/`)
- Assign your user to this group
- After that, the **Admin Panel** link will appear in the navbar and admin views will be accessible

---

## Production Notes (High Level)

Production setup is intentionally not stored in this repo, but the app has been used in a containerized environment with:

- Docker + docker-compose
- Gunicorn as WSGI server
- Nginx as reverse proxy
- Let’s Encrypt certificates (Certbot)
- PostgreSQL as the database

Those details are infrastructure‑specific, so they’re not required to understand or run the code locally.

---

## License

This project was built for educational and learning purposes.  
You’re free to read, learn from it, and adapt it to your own use cases.
