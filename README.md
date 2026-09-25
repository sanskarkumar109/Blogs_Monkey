# Production Blog Publishing SaaS Platform 🚀

A modern, high-performance, multi-user blog publishing SaaS application built with **Python 3.10**, **Django 4.2+**, **MySQL 8.0**, **Django REST Framework (DRF)**, **Tailwind CSS**, **HTMX**, and **Alpine.js**.

Designed following modern editorial aesthetics (Medium/Substack clean typography) paired with production-hardened SaaS architecture (IDOR protection, XSS sanitization, role-based access control, automated moderation, SEO optimization, and system analytics).

---

## 🌟 Architecture & Features

### 1. Core User Roles & Workflows
- **Anonymous Readers**: Public home page, blog listings, category & tag filtering, real-time search, author profiles, and reading progress indicators.
- **Authors & Writers**: Register, login, create draft posts, rich HTML content editing with `nh3` sanitization, save drafts, and submit posts for editorial review.
- **Admins & Editors**: Access to Operational Admin Portal (`/dashboard/admin/`), review submission queue, approve/publish or reject pending drafts, toggle featured status, feature categories, and manage users.

### 2. Modern 2026 Editorial Frontend
- **Design System**: Glassmorphism navigation, dark/light theme persistence via Alpine.js, responsive drawer menus, reading progress bar, table of contents generator.
- **Micro-Interactions**: Instant HTMX like and bookmark toggles without full page reloads.
- **SEO & Social Sharing**: Dynamic Open Graph meta tags, Twitter/X Cards, JSON-LD `BlogPosting` schema, auto-generated `sitemap.xml`, RSS feed (`/feed/`), and `robots.txt`.

### 3. Security & Production Hardening
- **XSS Prevention**: ORM-level HTML sanitization via `nh3` restricting safe tags (`p`, `h1`-`h6`, `b`, `i`, `a`, `img`, `code`, `pre`, `blockquote`, `ul`, `ol`, `li`).
- **IDOR & Ownership Controls**: Strict model-level and view-level authorization enforcing `blog.author == request.user`. Attempting unauthorized edits raises explicit `403 Forbidden`.
- **File Upload Security**: Upload validation for post covers verifying 5MB max file size and MIME magic byte signatures (`image/jpeg`, `image/png`, `image/webp`).
- **Dual Authentication**: Session authentication for web frontend and SimpleJWT (`Bearer` tokens) for REST API endpoints.

---

## 🛠 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.10 |
| **Web Framework** | Django 4.2+ |
| **Database** | MySQL 8.0 (PyMySQL driver) |
| **API Layer** | Django REST Framework & SimpleJWT |
| **Frontend Templates** | Django Templates, Tailwind CSS, Alpine.js |
| **Dynamic UX** | HTMX 1.9+ |
| **Sanitizer** | `nh3` (Rust-powered HTML sanitizer) |
| **WSGI Server** | Gunicorn (Linux VPS) |
| **Reverse Proxy** | Nginx |

---

## 📁 Repository Structure

```text
blog_platform/
├── apps/
│   ├── accounts/     # Custom User, Profile, Auth & User Management
│   ├── blog/         # Blog, Category, Tag, Workflow Models & Views
│   ├── content/      # Comments, Likes, Bookmarks, Reports & Health API
│   └── dashboard/    # Writer Dashboard & Operational Admin Portal
├── config/
│   ├── settings/
│   │   ├── base.py   # Base Django settings & DB setup
│   │   ├── dev.py    # Local development settings
│   │   └── prod.py   # Hardened production settings
│   ├── urls.py       # Global URL routing
│   └── wsgi.py       # WSGI entry point
├── templates/        # Modular HTML templates & layout wrappers
├── static/           # Styling, icons, scripts
├── media/            # Uploaded cover images
├── nginx/            # Production Nginx server configuration
├── .github/          # GitHub Actions CI workflow
├── gunicorn.conf.py  # Gunicorn process manager settings
├── manage.py         # Django CLI entrypoint
├── requirements.txt  # Production dependencies
└── README.md         # Project documentation
```

---

## 🚦 Quickstart Guide (Local Development)

### 1. Prerequisites
- Python 3.10+
- MySQL 8.0 running locally on `127.0.0.1:3306`

### 2. Virtual Environment & Dependencies
```bash
# Clone the repository
git clone https://github.com/sanskarkumar109/Blogs_Monkey.git
cd blog_platform

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your local MySQL credentials:
```bash
cp .env.example .env
```
Ensure your `.env` contains:
```env
DEBUG=True
SECRET_KEY=local-dev-secret-key
DB_ENGINE=django.db.backends.mysql
DB_NAME=blog_saas_db
DB_USER=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 4. Database Setup & Migrations
```bash
# Create MySQL Database
mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS blog_saas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
python manage.py migrate

# Create initial superuser/admin account
python manage.py createsuperuser
```

### 5. Launch Development Server
```bash
python manage.py runserver 8000
```
Visit `http://127.0.0.1:8000` in your web browser.

---

## 🧪 Testing & Verification

Execute the complete automated test suite (34 tests across models, forms, auth, authorization, search, and health endpoints):
```bash
python manage.py test accounts.tests blog.tests content.tests dashboard.tests
```

Run deployment safety checks:
```bash
python manage.py check --deploy --settings=config.settings.prod
```

---

## 📡 API Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/token/` | Obtain JWT access & refresh pair | No |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh JWT access token | No |
| `GET` | `/api/v1/search/autocomplete/` | Search posts/authors auto-suggestions | No |
| `GET` | `/dashboard/api/v1/stats/` | Platform metrics & user analytics | Yes (Admin/Staff) |
| `GET` | `/health/` | System status & DB connection check | No |

---

## 📄 License & Contact
Distributed under the MIT License. Designed for high-concurrency SaaS deployments.
