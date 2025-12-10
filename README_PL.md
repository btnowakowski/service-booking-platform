# Accommodations – System rezerwacji w Django

**Accommodations** to niewielki, ale w pełni produkcyjny system rezerwacji zbudowany w Django.  
Aplikacja pozwala użytkownikom przeglądać dostępne usługi, rezerwować wolne terminy w widoku kalendarza oraz śledzić status swoich rezerwacji.  
Administratorzy otrzymują dedykowany panel, w którym mogą zarządzać usługami, terminami oraz akceptować lub odrzucać rezerwacje.

Repozytorium zawiera projekt Django oraz Dockerfile do budowania obrazu aplikacji, ale nie zawiera pełnej infrastruktury serwerowej (brak docker-compose, konfiguracji nginx, certyfikatów, skryptów wdrożeniowych).
Repo jest celowo uproszczone — czytelne, zrozumiałe i przygotowane do wygodnego uruchomienia lokalnie.


---

## Najważniejsze funkcje

### Dla użytkowników
- Lista usług (nazwa, opis, cena)
- Podstrona usługi z interaktywnym kalendarzem (FullCalendar)
- Rezerwacja poprzez kliknięcie w wolny termin
- Rejestracja, logowanie i wylogowanie użytkownika
- Panel „Moje rezerwacje”:
  - przegląd własnych rezerwacji
  - filtrowanie po statusie i usłudze
  - jasne, polskie etykiety statusów:
    - `Oczekująca`
    - `Zatwierdzona`
    - `Anulowana`
    - `Odrzucona`

### Dla administratorów (niestandardowy panel)
Dedykowany panel administracyjny (inny niż Django `/admin/`), dostępny pod:

- `/admin-panel/`

Funkcje:
- Dashboard ze statystykami:
  - liczba wszystkich rezerwacji
  - liczba rezerwacji oczekujących / zatwierdzonych / anulowanych / odrzuconych
- Szybkie akcje:
  - akceptacja / odrzucenie rezerwacji z poziomu listy
- Zarządzanie usługami:
  - dodawanie, edycja, usuwanie
- Zarządzanie terminami:
  - dodawanie, edycja, usuwanie
  - włączanie / wyłączanie aktywności terminów (`is_active`)
- Spójny, ciemny motyw UI
<img width="1020" height="857" alt="image" src="https://github.com/user-attachments/assets/32e3f528-f531-47be-a0c7-fad4db9f8a84" />


### UX i UI
- Globalny ciemny motyw (custom CSS: `booking/static/booking/style.css`)
- Responsywny układ oparty na Bootstrapie 5
- Spójna nawigacja:
  - usługi
  - moje rezerwacje
  - panel administratora (tylko dla grupy admin)
- Widok kalendarza:
  - widok tygodnia / dnia
  - pełna lokalizacja PL
  - ukrywanie kalendarza, gdy brak wolnych terminów
  - komunikaty pomocnicze dla użytkownika

---

## Stos technologiczny

- **Backend:** Django 5
- **Baza danych:** PostgreSQL (produkcyjnie), lokalnie możliwa SQLite
- **Frontend:** Django templates, Bootstrap 5, FullCalendar
- **Auth:** Django auth, własny formularz logowania (`CustomAuthForm`), rejestracja
- `.env` i `python-dotenv` do konfiguracji środowiska
- Oddzielony panel aplikacji i panel Django

---

## Uruchamianie projektu lokalnie

Poniższe kroki pozwalają uruchomić projekt lokalnie w kilka minut.

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/btnowakowski/service-booking-platform
cd mvc_projekt_semestralny
```

### 2. Wirtualne środowisko

```bash
python -m venv .venv
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 4. Konfiguracja środowiska (`.env`, opcjonalne ale zalecane)

Utwórz plik `.env`:

```env
DJANGO_SECRET_KEY=twoj-sekret-dev
DJANGO_DEBUG=1
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost
```

Dla prostego uruchomienia możesz tymczasowo użyć SQLite:

```python
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }
```

### 5. Włączenie panelu Django admin (domyślnie wyłączony)

Otwórz plik:

```
mvc_projekt_semestralny/urls.py
```

Odkomentuj linię:

```python
path("admin/", admin.site.urls),
```

Panel będzie dostępny pod:
http://127.0.0.1:8000/admin/

### 6. Migracje

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Superuser (opcjonalne, potrzebne do `/admin/`)

```bash
python manage.py createsuperuser
```

### 8. Uruchomienie serwera developerskiego

```bash
python manage.py runserver
```

Aplikacja będzie dostępna pod:

- Główna strona: http://127.0.0.1:8000/  
- Django admin: http://127.0.0.1:8000/admin/  
- Panel aplikacji: http://127.0.0.1:8000/admin-panel/  

---

## Grupy i uprawnienia

Aby uzyskać dostęp do panelu administracyjnego aplikacji:

1. Wejdź do `/admin/`
2. Dodaj grupę o nazwie **`Admin`**
3. Przypisz użytkownika do tej grupy

Po tym w menu pojawi się link **Admin Panel**.

---

## Uruchomienie z Docker Compose

Najszybszy sposób na uruchomienie projektu lokalnie.

### Opcja 1: Pełny stack (Django + PostgreSQL)

```bash
# Uruchom aplikację z bazą PostgreSQL
docker-compose up --build

# W drugim terminalu wykonaj migracje i utwórz superusera
docker exec -it booking_web python manage.py migrate
docker exec -it booking_web python manage.py createsuperuser
```

Aplikacja będzie dostępna pod: http://localhost:8000/

### Opcja 2: Tryb deweloperski (Django + SQLite)

```bash
# Uruchom tylko aplikację bez Postgres
docker-compose --profile dev up web-dev --build
```

### Przydatne komendy Docker

```bash
# Zatrzymanie kontenerów
docker-compose down

# Zatrzymanie + usunięcie wolumenów (czysta baza)
docker-compose down -v

# Logi
docker-compose logs -f web

# Wejście do kontenera
docker exec -it booking_web bash
```

---

## Uwaga o produkcji (wysoki poziom)

W repozytorium znajduje się `Dockerfile` oraz `docker-compose.yml` do testowania lokalnego.  
Projekt działał produkcyjnie w środowisku opartym o:

- Docker + docker-compose  
- Gunicorn  
- Nginx jako reverse proxy  
- Certbot (Let's Encrypt)  
- PostgreSQL  

---

## Licencja

Projekt powstał jako materiał edukacyjny.  
Możesz z niego swobodnie korzystać, uczyć się i dostosowywać do własnych potrzeb.
