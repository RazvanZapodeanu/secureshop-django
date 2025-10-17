# 🔒 Security Equipment Store

A Django-based e-commerce platform for security and surveillance equipment.

## Tech Stack

- **Backend:** Django 5.2.7 · PostgreSQL  
- **Frontend:** HTML5 · CSS3


## Features

- Product catalog with categories, tags, and manufacturers
- Dynamic discount system with time-based promotions
- Custom visit tracking middleware
- PostgreSQL database with interconnected models


##  Database Schema

Products · Manufacturers · Categories · Tags · Specifications · Reviews · Discounts

## Installation
### Prerequisites
- Python 3.8+
- PostgreSQL
---
**Setup database:**
```
CREATE DATABASE secured_db;
CREATE USER secured_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE secured_db TO secured_user;
```
**Clone:**
```
git clone https://github.com/RazvanZapodeanu/secureshop-django.git
cd secureshop-django
pipenv install && pipenv shell
```

**Configure** `.env`:
```
SECRET_KEY=your-secret-key
DB_NAME=secured_db
DB_USER=secured_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```
**Generate SECRET_KEY:**
```
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```
**Initialize:**
```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```




##  Pages

- `/` - Homepage with product categories
- `/despre/` - About us page
- `/produse/` - Product catalog
- `/info/` - Server information and parameters
- `/log/` - Visit tracking and analytics
- `/admin/` - Django admin panel

---
⚠️ **This is a development project.**
