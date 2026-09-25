# Production Deployment Guide 🚀

This document outlines the step-by-step production deployment process for the Blog SaaS Platform on an **Ubuntu 22.04 LTS / 24.04 LTS VPS** using **Nginx**, **Gunicorn**, **MySQL 8.0**, and **Certbot SSL**.

---

## 📋 Infrastructure Prerequisites

- Ubuntu 22.04 LTS or 24.04 LTS VPS (1 vCPU, 2GB RAM minimum recommended)
- Fully Qualified Domain Name (e.g., `yourdomain.com` pointing to VPS IP)
- Root or `sudo` SSH access to the server

---

## 🚀 Step-by-Step Deployment Walkthrough

### Step 1: System Package Update & Installation
SSH into your Ubuntu server and install base OS dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv mysql-server nginx git curl ufw
```

---

### Step 2: Configure Production MySQL 8.0 Database
Run the MySQL security script and configure a dedicated database user:
```bash
sudo mysql_secure_installation
```

Log into MySQL shell as root:
```bash
sudo mysql
```

Execute SQL commands to create database and user:
```sql
CREATE DATABASE blog_saas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'blog_user'@'localhost' IDENTIFIED BY 'STRONG_DB_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON blog_saas_db.* TO 'blog_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Verify connection:
```bash
mysql -u blog_user -pSTRONG_DB_PASSWORD_HERE blog_saas_db -e "STATUS;"
```

---

### Step 3: Clone Codebase & Setup Python Environment
Create deployment directory and set permissions:
```bash
sudo mkdir -p /var/www/blog_platform
sudo chown -R $USER:$USER /var/www/blog_platform
cd /var/www/blog_platform

# Clone from GitHub
git clone https://github.com/yourusername/blog_platform.git .

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install production dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: Configure Production Environment (`.env`)
Create production environment file `/var/www/blog_platform/.env`:
```bash
cp .env.example .env
nano .env
```

Set secure production values:
```env
SECRET_KEY=generate-a-64-character-random-key-here-with-python-c-import-secrets;print(secrets.token_urlsafe(50))
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,127.0.0.1

DB_ENGINE=django.db.backends.mysql
DB_NAME=blog_saas_db
DB_USER=blog_user
DB_PASSWORD=STRONG_DB_PASSWORD_HERE
DB_HOST=127.0.0.1
DB_PORT=3306

JWT_SECRET_KEY=generate-another-random-jwt-signing-key
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_smtp_key
DEFAULT_FROM_EMAIL=SaaS Blog Platform <noreply@yourdomain.com>
```

---

### Step 5: Execute Migrations, Static Collection & Superuser Creation
```bash
source venv/bin/activate

# Apply database migrations against MySQL
python manage.py migrate --settings=config.settings.prod

# Collect static files to staticfiles/ directory
python manage.py collectstatic --noinput --settings=config.settings.prod

# Create initial admin user
python manage.py createsuperuser --settings=config.settings.prod
```

Set permissions for `staticfiles` and `media`:
```bash
sudo chown -R www-data:www-data /var/www/blog_platform/media
sudo chown -R www-data:www-data /var/www/blog_platform/staticfiles
sudo chmod -R 775 /var/www/blog_platform/media
```

---

### Step 6: Configure Gunicorn Systemd Service
Create systemd service file for Gunicorn at `/etc/systemd/system/gunicorn.service`:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Insert configuration:
```ini
[Unit]
Description=Gunicorn daemon for Blog SaaS Platform
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/blog_platform
ExecStart=/var/www/blog_platform/venv/bin/gunicorn --config /var/www/blog_platform/gunicorn.conf.py config.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start Gunicorn:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

---

### Step 7: Configure Nginx & Setup SSL via Let's Encrypt
Copy the repository Nginx config file to Nginx sites-available:
```bash
sudo cp /var/www/blog_platform/nginx/blog_platform.conf /etc/nginx/sites-available/blog_platform
sudo ln -s /etc/nginx/sites-available/blog_platform /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

Test Nginx syntax:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

Install Certbot and obtain SSL certificates:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically update the Nginx configuration to enforce HTTPS redirection and install SSL certificates.

---

## 🔄 Maintenance & Operational Runbook

### 1. How to Deploy Updates (Zero-Downtime Migration)
```bash
cd /var/www/blog_platform
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=config.settings.prod
python manage.py collectstatic --noinput --settings=config.settings.prod
sudo systemctl reload gunicorn
```

### 2. Service Management
```bash
# Restart Gunicorn
sudo systemctl restart gunicorn

# Reload Nginx
sudo systemctl reload nginx

# Check Statuses
sudo systemctl status gunicorn
sudo systemctl status nginx
```

### 3. Database Backup & Restore

#### Automated MySQL Backup Script
Create `/usr/local/bin/backup_blog_db.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/mysql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR
mysqldump -u blog_user -p'STRONG_DB_PASSWORD_HERE' blog_saas_db | gzip > "$BACKUP_DIR/blog_saas_db_$TIMESTAMP.sql.gz"
find $BACKUP_DIR -type f -mtime +14 -name "*.sql.gz" -delete
```
Make executable and add to crontab (runs daily at 2:00 AM):
```bash
sudo chmod +x /usr/local/bin/backup_blog_db.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup_blog_db.sh") | crontab -
```

#### Database Restore Procedure
```bash
gunzip -c /var/backups/mysql/blog_saas_db_20260921_020000.sql.gz | mysql -u blog_user -pSTRONG_DB_PASSWORD_HERE blog_saas_db
```

### 4. Log Inspection & Debugging
```bash
# Gunicorn Logs
sudo tail -n 100 /var/log/gunicorn/error.log
sudo tail -n 100 /var/log/gunicorn/access.log

# Django Error Logs
tail -n 100 /var/www/blog_platform/logs/django_errors.log

# Nginx Logs
sudo tail -n 100 /var/log/nginx/error.log

# Systemd Journal
sudo journalctl -u gunicorn -e --no-pager
```

### 5. Secrets Rotation Procedure
To rotate `SECRET_KEY` or `JWT_SECRET_KEY`:
1. Generate new keys using `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
2. Update `/var/www/blog_platform/.env`.
3. Reload Gunicorn: `sudo systemctl restart gunicorn`.
