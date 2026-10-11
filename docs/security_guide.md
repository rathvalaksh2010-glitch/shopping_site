# Security Guide

## Single-Shop E-commerce Website

### 1. Security Objectives

Protect customer accounts, personal information, orders, inventory, administrative functionality, and payment operations against unauthorized access, data leakage, fraud, and accidental corruption.

Apply least privilege, server-side validation, secure defaults, and defense in depth.

### 2. Password Security

* Never store plaintext passwords or reversible password encryption.
* Use Werkzeug's `generate_password_hash()` and `check_password_hash()` or a suitable modern password-hashing implementation.
* Prefer a supported scrypt or Argon2id configuration with appropriate parameters.
* Enforce sensible minimum password requirements and allow long passphrases.
* Do not silently truncate passwords.
* Rate-limit login and password-reset attempts.
* Return generic login failures to reduce account enumeration.
* Use a secure password-reset flow with random, single-use, expiring tokens.
* Invalidate used reset tokens and relevant sessions after password changes.
* Never log passwords, reset tokens, or authentication secrets.

### 3. Authentication and Session Security

* Use a maintained authentication extension such as Flask-Login.
* Store only necessary session data; never store passwords or payment details in the session.
* Set session cookies with `Secure`, `HttpOnly`, and an appropriate `SameSite` policy.
* Set Flask's session lifetime and expiration policy deliberately.
* Regenerate or replace the session after login and privilege changes where appropriate.
* Clear the session on logout.
* Reauthenticate before sensitive account changes.
* Consider stronger authentication for administrators, including multi-factor authentication.

### 4. Authorization and Admin Protection

* Enforce role checks on the server for every admin route and sensitive operation.
* Hiding an admin link in HTML is not access control.
* Default new accounts to the customer role.
* Never accept a user-supplied role during public registration.
* Do not authorize users based only on an object ID or URL.
* Ensure customers can access only their own addresses, carts, and orders.
* Restrict admin account creation and role changes to a trusted process.
* Audit sensitive administrative actions.

Example:

```
from functools import wraps
from flask import abort
from flask_login import current_user, login_required

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped
```

Use the decorator on admin views and test both direct URL access and submitted requests. This example assumes that the user model and login configuration are correctly implemented.

### 5. CSRF Protection

* Enable CSRF protection for state-changing forms.
* Use Flask-WTF or another maintained CSRF implementation.
* Include valid CSRF tokens in POST forms.
* Never use GET requests to add products, delete items, update inventory, or place orders.
* Protect account, checkout, and admin actions.
* Payment webhooks are not ordinary browser forms; verify their provider signatures and follow the provider's webhook requirements.

### 6. SQL Injection Protection

* Use SQLAlchemy's parameterized queries and ORM operations.
* Never concatenate untrusted input into SQL strings.
* Validate sorting fields and filter parameters against explicit allowlists.
* Avoid raw SQL unless necessary and parameterized correctly.
* Use database constraints to enforce uniqueness and valid relationships.

### 7. XSS and HTML Injection

* Use Jinja's automatic HTML escaping.
* Avoid rendering customer or admin input with the `safe` filter.
* Sanitize rich HTML content with a maintained allowlist sanitizer if rich-text input is required.
* Validate product descriptions, category names, and uploaded metadata.
* Set a suitable Content Security Policy.
* Avoid inserting untrusted values into JavaScript, HTML attributes, or CSS without context-appropriate handling.

### 8. Input Validation and Business Logic

Validate all untrusted data on the server, including:

* Email addresses and required fields.
* Quantity as a positive integer within reasonable limits.
* Product and category IDs.
* Address and postal-code fields.
* Product price and stock changes.
* Order-status transitions.
* Image type, size, and content.
* Payment callback data.

Never trust:

* A price sent by the browser.
* A total calculated by JavaScript.
* A stock quantity sent by a customer.
* A user ID submitted in a form.
* A client-side claim that payment succeeded.

Recalculate order totals using current server-side data.

### 9. Inventory and Checkout Integrity

* Use database transactions for order creation and stock changes.
* Prevent negative inventory with conditional updates or appropriate row-level locking.
* Add database constraints where possible.
* Ensure checkout retries cannot create duplicate orders.
* Verify payment webhooks and handle duplicate delivery safely.
* Maintain an inventory movement history.
* Define reservation expiry and stock-release rules.
* Never mark an order as paid based only on a redirect to a success page.

### 10. Payment Security

* Prefer a reputable payment gateway with hosted checkout or tokenized payment handling.
* Do not collect or store raw card numbers or CVVs.
* Keep payment secrets on the server.
* Verify webhook signatures and relevant order, amount, currency, and transaction references.
* Make payment operations idempotent.
* Log payment state transitions without recording sensitive credentials.
* Handle payment failures, cancellations, delayed notifications, and refunds.
* Confirm applicable payment-provider and PCI DSS obligations before launch.

### 11. File Upload Security

* Allow only required image formats.
* Validate file size and actual file content, not just the filename extension.
* Generate server-controlled filenames.
* Do not use a user-provided filename as a filesystem path.
* Prevent path traversal.
* Store uploads in a non-executable location.
* Restrict permissions and consider image re-encoding.
* Avoid accepting HTML, scripts, or arbitrary executable files as product images.

### 12. Rate Limiting and Abuse Prevention

Apply limits to:

* Login and registration.
* Password reset.
* Product search where abuse is possible.
* Checkout and payment initiation.
* Contact or feedback forms.
* Sensitive admin actions.

Use a maintained rate-limiting extension, and consider a shared backend for limits in multi-worker deployments.

### 13. Secrets and Environment Variables

* Generate a cryptographically random Flask secret key.
* Keep credentials out of Git.
* Add `.env`, local databases, private uploads, logs, and other sensitive artifacts to `.gitignore` as appropriate.
* Provide `.env.example` with placeholders only.
* Rotate secrets that have been exposed.
* Use separate development and production credentials.
* Restrict production secret access.

### 14. HTTP and Browser Security

Configure:

* HTTPS and HTTP-to-HTTPS redirection at the deployment layer.
* HSTS after HTTPS deployment is verified.
* `X-Content-Type-Options: nosniff`.
* A suitable `Content-Security-Policy`.
* Appropriate clickjacking protection, such as `frame-ancestors`.
* A restrictive referrer policy.
* Secure cookie attributes.

Set headers using a maintained security extension or carefully tested middleware. Ensure the deployment proxy is configured correctly.

### 15. Privacy and Data Protection

* Collect only information needed to operate the shop.
* Explain data collection and use in the privacy policy.
* Establish retention periods for customer and order information.
* Restrict access to personal data.
* Protect backups and logs.
* Provide appropriate ways to handle privacy requests.
* Avoid logging full addresses, passwords, session tokens, or payment details unnecessarily.
* Review applicable Indian data-protection, consumer-protection, tax, and e-commerce requirements before launch.

The privacy policy must accurately describe actual website behavior and third-party integrations; it must not be a generic promise that the implementation does not meet.

### 16. Error Handling and Monitoring

* Disable Flask debug mode in production.
* Show generic error pages to users.
* Record detailed errors in protected server logs.
* Never expose stack traces, secrets, SQL statements, or environment variables to customers.
* Monitor repeated login failures, unauthorized admin access, inventory anomalies, and payment errors.
* Restrict log access and retention.

### 17. Backup and Recovery

* Schedule database backups.
* Encrypt backups where appropriate.
* Restrict backup access.
* Maintain a documented restore procedure.
* Test restoration periodically.
* Back up required product images and other persistent assets.
* Define acceptable recovery time and data-loss objectives.

### 18. Pre-Launch Security Checklist

* [ ] Password hashing and password-reset flow tested.
* [ ] Customer and admin permissions tested.
* [ ] CSRF protection enabled.
* [ ] SQL injection and XSS protections reviewed.
* [ ] Session cookies configured securely.
* [ ] Login and checkout rate limits configured.
* [ ] Upload validation tested.
* [ ] Stock concurrency and negative-stock tests passed.
* [ ] Order and payment idempotency tested.
* [ ] Payment webhook verification implemented, if applicable.
* [ ] Secrets removed from source control.
* [ ] Debug mode disabled.
* [ ] HTTPS and security headers configured.
* [ ] Privacy policy and terms reviewed.
* [ ] Backups and restoration tested.
* [ ] Dependencies reviewed for known vulnerabilities.
* [ ] Production access and logging reviewed.

### 19. Incident Response

If a security incident occurs:

1. Contain the affected account, service, or credential.
2. Preserve relevant logs and evidence.
3. Rotate exposed secrets and revoke compromised sessions.
4. Determine which systems and personal data were affected.
5. Restore trusted systems where necessary.
6. Notify affected parties and authorities when required.
7. Document the cause and implement preventive fixes.
