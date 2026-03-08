# Secured Systems — Security Equipment Store

E-commerce platform built with Django for selling professional security and surveillance equipment.

## Tech Stack

- **Backend:** Django
- **Database:** PostgreSQL
- **Frontend:** Django templates, vanilla CSS, localStorage for cart persistence
- **Scheduling:** APScheduler via django-apscheduler
- **PDF Generation:** ReportLab (invoice generation on order placement)

## Project Structure

```
core/                   # Django project config (settings, urls, wsgi)
products/
├── models.py           # 13 models — Product, Utilizator (AbstractUser), Order, etc.
├── views.py            # ~1000 lines — all view logic
├── forms.py            # 7 forms with custom validators
├── admin.py            # Customized admin panel with fieldsets and inlines
├── middleware.py        # Visit tracking middleware (logs IP, URL, timestamp)
├── tasks.py            # 4 scheduled background tasks
├── signals.py          # Post-save signal handlers
├── sitemaps.py         # SEO sitemaps
├── context_processors.py   # Global context: dynamic category menu, business hours
├── templatetags/
│   └── custom_tags.py  # Product of the day, EUR price conversion, recent views
├── templates/products/ # 20+ HTML templates
└── static/products/    # CSS, images
```

## Features

### Authentication & Security
- Custom user model extending `AbstractUser` with phone, address, postal code, birth date
- Email confirmation flow with unique token generation (`secrets.token_urlsafe`)
- Login with "remember me" (session expiry control), failed login tracking per IP
- Automatic admin notification via `mail_admins` after 3+ failed login attempts from same IP
- Account blocking system, email confirmation enforcement before login
- Password change with `update_session_auth_hash` to keep session alive
- Permission-based access control (custom `vizualizeaza_oferta` permission created at app startup)
- Custom 403 page with session-tracked error count — auto-blocks after N attempts (configurable via `settings.N_MAX_403`)

### Product Catalog
- Advanced filtering form: by name, manufacturer, category, tag, price range, stock range, product code, availability
- Sorting by price (ascending/descending), pagination with configurable items per page
- Pagination change detection — warns user about potential skipped/duplicate products
- Products with zero stock automatically pushed to end of listing
- Active discount calculation with time-based validation (`data_inceput` / `data_sfarsit`)
- Category-specific product pages with locked category filter
- Product detail page with specs, reviews, average rating
- Caching: pagination preference stored in both session and cache (5-day TTL)

### Shopping & Orders
- Cart implemented in localStorage (client-side persistence)
- Order placement via JSON POST — stock validation, auto-decrement, PDF invoice generation
- Invoice PDF created with ReportLab: styled table with product details, totals, company branding
- Invoices saved to `media/temporar-facturi/{username}/` with timestamp
- Email notification on order (console backend in dev)

### Contact System
- Complex form with 10+ fields and layered validation:
  - CNP validation (checksum, date extraction, cross-check with birth date field)
  - Age verification (must be 18+)
  - Email confirmation (dual field match)
  - Message word count (5–100), max word length (15 chars), no links allowed
  - Message must end with sender's name (signature enforcement)
  - Dynamic minimum wait days based on message type (review/request: 4 days, question: 2 days)
  - Temporary email domain blocking (guerillamail, yopmail)
- Messages saved as JSON files with metadata (IP, timestamp, urgency flag)
- Auto text formatting: collapse whitespace, capitalize after sentence-ending punctuation

### Scheduled Tasks (APScheduler)
- **Unconfirmed user cleanup** — runs every K minutes, deletes users who never confirmed email
- **Newsletter** — weekly on configurable day/hour, sends product recommendations to confirmed users
- **Stock sync** — every 30 min, syncs `disponibil` flag with actual stock count
- **Profile completion reminder** — daily at 09:00, flags users missing phone/address (respects N-day cooldown)

### Admin Panel
- Customized `ModelAdmin` for all 13 models
- Fieldsets with collapsible sections (product descriptions, media, classification)
- Inline editing: product specifications (TabularInline), order items
- Custom filters, search fields, ordering, pagination per model
- `UserAdmin` extended with extra fieldsets for custom user fields

### Other
- **Visit tracking middleware** — logs every request (IP, full URL, timestamp) in memory, queryable via `/log/` with URL params (`?ultimele=N`, `?tabel=tot`, `?sql=true`, `?accesari=nr`)
- **Custom template tags** — product of the day (cached until midnight), price in EUR (configurable exchange rate), last viewed products (per user, today only)
- **Context processors** — dynamic category menu from DB, business hours status (configurable weekly schedule)
- **Logging** — 5-level file logging (debug, info, warning, error, critical) + console + admin email handler
- **Sitemaps** — static pages, product pages, category pages, generic sitemap
- **Promotions** — admin creates promotions per category, triggers mass email to users who viewed products in those categories (threshold: `MIN_VIZUALIZARI_PROMOTIE`)
- **Rating system** — one rating per user per product, enforced at DB level (`unique_together`)
- **EUR conversion** — template filter and tag using configurable `CURS_EUR` from settings

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL

### Database

```sql
CREATE DATABASE secured_db;
CREATE USER secured_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE secured_db TO secured_user;
```

### Install

```bash
git clone https://github.com/RazvanZapodeanu/secureshop-django.git
cd secureshop-django
pip install -r requirements.txt
```

### Environment

Create `.env` in root:

```
SECRET_KEY=your-secret-key
DB_NAME=secured_db
DB_USER=secured_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

Generate a secret key:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin panel: `http://localhost:8000/hidden/`

## Routes

| Route | Access | Description |
|-------|--------|-------------|
| `/` | Public | Homepage, product of the day |
| `/produse/` | Public | Catalog with filters and pagination |
| `/produs/<slug>/` | Public | Product detail, specs, reviews |
| `/categorii/<slug>/` | Public | Category-filtered product listing |
| `/despre/` | Public | About page |
| `/contact/` | Public | Contact form with complex validation |
| `/cos_virtual/` | Public | Shopping cart (localStorage) |
| `/inregistrare/` | Public | Registration with email confirmation |
| `/login/` | Public | Login with brute-force detection |
| `/profil/` | Auth | User profile |
| `/editare-profil/` | Auth | Edit profile |
| `/schimba-parola/` | Auth | Change password |
| `/promotii/` | Auth | Create promotions (mass email) |
| `/oferta/` | Permission | Special offer (requires custom permission) |
| `/adauga-produs/` | Permission | Add product form |
| `/info/` | Admin | Server info, request params |
| `/log/` | Admin | Visit log with query options |
| `/hidden/` | Staff | Django admin panel |

## Status

This is a university project that covers a wide range of Django features. Some things that are in progress:

- `finalizeaza_comanda` view returns a placeholder page
- `signals.py` has an empty `post_save` handler for `Comanda`
- Email backend is set to console (no real emails sent)
- No automated tests