# Security Policy & Vulnerability Mitigation 🛡️

This document outlines the security architecture, threat model, authorization constraints, and vulnerability handling practices enforced in the **Blog SaaS Platform**.

---

## 🔒 Security Architecture Overview

### 1. Cross-Site Scripting (XSS) Prevention
- **HTML Content Sanitization**: All user-submitted blog post content and comments undergo ORM-level HTML sanitization using `nh3` (a Rust-powered HTML sanitizer). Only explicit white-listed tags (`p`, `h1`-`h6`, `b`, `i`, `a`, `img`, `blockquote`, `code`, `pre`, `ul`, `ol`, `li`) and attributes (`href`, `src`, `alt`, `title`, `class`) are preserved.
- **Template Escaping**: Django auto-escaping is active across all templates. The `|safe` filter is strictly restricted to fields already sanitized by `nh3`.

### 2. Insecure Direct Object Reference (IDOR) & Ownership Protection
- **Object-Level Authorization**: Every update, edit, draft save, and deletion view enforces ownership checks:
  ```python
  if blog.author != request.user and not request.user.is_staff:
      raise PermissionDenied("You cannot modify another user's post.")
  ```
- **Admin Isolation**: Operational admin views (`/dashboard/admin/`) require `@user_passes_test(is_admin)`, preventing non-staff users from accessing submission queues, publishing posts, or viewing platform metrics.

### 3. Cross-Site Request Forgery (CSRF) Protection
- All HTML forms contain `{% csrf_token %}`.
- Dynamic HTMX requests include the `X-CSRFToken` header.
- `CSRF_COOKIE_HTTPONLY = True`, `CSRF_COOKIE_SECURE = True`, and `CSRF_COOKIE_SAMESITE = 'Lax'` are enforced in production settings.

### 4. SQL Injection Protection
- All database queries interact strictly through the Django ORM using parameterized queries. Raw SQL formatting and unescaped queries are prohibited.

### 5. File Upload Verification
- Cover images uploaded by users are validated prior to disk persistence:
  - **File Size**: Capped at 5MB maximum (`5 * 1024 * 1024` bytes).
  - **Magic Bytes Verification**: File headers are parsed using Python `Pillow` to verify genuine MIME types (`image/jpeg`, `image/png`, `image/webp`).
  - **Filename Sanitization**: Upload paths use random UUIDs or sanitized slugs to prevent directory traversal attacks.

---

## 🛡️ Production Security Headers Matrix

| Header | Setting | Purpose |
| :--- | :--- | :--- |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Forces HTTPS for 1 year |
| `X-Frame-Options` | `DENY` | Prevents Clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-XSS-Protection` | `1; mode=block` | Browser XSS filter |
| `Referrer-Policy` | `same-origin` | Prevents referrer leakage |
| `Session Cookie` | `HttpOnly`, `Secure`, `SameSite=Lax` | Protects session tokens from theft |

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability within this repository, please do **NOT** file a public GitHub issue.

Please report security concerns directly to:
- **Security Contact**: `security@yourdomain.com`

Include:
- Step-by-step proof-of-concept (PoC)
- Impact assessment
- Proposed patch or mitigation if available

We respond to security disclosures within 24 hours.
