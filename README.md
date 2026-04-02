# CanteenPOS Setup Guide

This is a complete, modern billing and inventory management system built with Django and Bootstrap 5.

## 🚀 Quick Start (Development)

The system is already configured with SQLite and seeded with starting data in this environment. To run it locally:

1. Open a terminal in the `canteenbilling` folder
2. Activate your virtual environment (if using one) or ensure dependencies are installed:
   ```bash
   pip install django mysqlclient Pillow reportlab django-crispy-forms crispy-bootstrap5
   ```
3. Start the Django development server:
   ```bash
   python manage.py runserver
   ```
4. Open your browser and navigate to `http://127.0.0.1:8000/`

---

## 🔐 Default Credentials

The database has been seeded with three roles for testing:

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Admin** | `admin` | `admin123` | Full system access, User Management, Reports |
| **Manager** | `manager` | `manager123` | POS, Inventory, Reports |
| **Cashier** | `cashier` | `cashier123` | POS Billing only |

---

## 🛠️ Production Setup (MySQL)

By default, the project uses SQLite for easy development. To switch to MySQL for production:

1. Open `canteen/settings.py`
2. Comment out the default SQLite `DATABASES` dictionary (around line 52).
3. Uncomment the MySQL configuration below it:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'canteen_billing',
           'USER': 'root',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '3306',
           'OPTIONS': {
               'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
           }
       }
   }
   ```
4. Create the MySQL database: `CREATE DATABASE canteen_billing;`
5. Run migrations: `python manage.py migrate`
6. Run the seed script to populate test data: `python seed.py`

---

## 🧩 Features Implemented

* **Modern Dark/Light UI**: Premium aesthetic with micro-animations and Bootstrap 5 + custom CSS.
* **POS Module**: Grid-based layout, keyboard shortcuts (F2, F4, Esc), cart management, tax calculation, and payment modal.
* **Inventory Control**: Real-time stock alerts, item threshold indicators, stock movement history.
* **Role-Based Routing**: Strict access limitations for cashiers vs managers vs admins.
* **Responsive Dashboards**: Chart.js integration for sales data and top-selling categories.
* **Reciepts**: Printable receipt generation format matching thermal printers.
* **Data Export**: CSV report generation for selected periods.
