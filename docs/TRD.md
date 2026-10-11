# Technical Requirements Document (TRD)

## Single-Shop E-commerce Website

### 1. Technology Stack

| Layer                    | Technology                                                            |
| ------------------------ | --------------------------------------------------------------------- |
| Programming language     | Python                                                                |
| Backend framework        | Flask                                                                 |
| Frontend                 | HTML5, CSS3                                                           |
| Client-side interactions | Vanilla JavaScript, when needed                                       |
| Database                 | PostgreSQL for production; SQLite for initial development             |
| ORM                      | Flask-SQLAlchemy / SQLAlchemy                                         |
| Database migrations      | Flask-Migrate                                                         |
| Authentication           | Flask-Login                                                           |
| Form validation and CSRF | Flask-WTF / WTForms                                                   |
| Password hashing         | Werkzeug security utilities                                           |
| Testing                  | pytest                                                                |
| Production server        | Gunicorn on compatible Linux hosting                                  |
| Static files and images  | Local storage for development; suitable object storage for production |

Pin compatible dependency versions in a requirements file. Do not use Flask's development server as the production server.

### 2. Application Architecture

Use a modular Flask application factory pattern.

Recommended structure:

project/

* app/

  * **init**.py
  * extensions.py
  * models/

    * user.py
    * product.py
    * category.py
    * cart.py
    * order.py
    * inventory.py
    * shop_settings.py
  * blueprints/

    * auth/
    * main/
    * products/
    * cart/
    * checkout/
    * orders/
    * admin/
  * services/

    * pricing.py
    * inventory.py
    * order_service.py
    * payment_service.py
  * templates/

    * base.html
    * home.html
    * auth/
    * products/
    * cart/
    * checkout/
    * orders/
    * admin/
    * legal/
  * static/

    * css/
    * js/
    * images/
  * forms.py
  * config.py
* migrations/
* tests/
* instance/
* .env.example
* .gitignore
* requirements.txt
* run.py

Keep business logic in service functions instead of placing all logic inside route handlers.

### 3. Database Design

#### Users

* `id` — primary key.
* `name`.
* `email` — unique.
* `password_hash`.
* `role` — customer or admin.
* `is_active`.
* `created_at`, `updated_at`.

#### Addresses

* `id`.
* `user_id` — foreign key.
* `recipient_name`.
* `phone`.
* `address_line_1`, `address_line_2`.
* `city`, `state`, `postal_code`, `country`.

#### Categories

* `id`.
* `name`.
* `slug` — unique.
* `description`.
* `is_active`.

#### Products

* `id`.
* `category_id` — foreign key.
* `name`.
* `slug` — unique.
* `description`.
* `price` — decimal, not floating point.
* `image_path`.
* `is_active`.
* `created_at`, `updated_at`.

#### Inventory

* `product_id` — primary key and foreign key.
* `quantity_available`.
* `low_stock_threshold`.
* `updated_at`.

#### Inventory Movements

* `id`.
* `product_id`.
* `quantity_change`.
* `reason`.
* `reference_type`.
* `reference_id`.
* `created_by`.
* `created_at`.

Record stock changes as auditable events. Do not rely only on the current stock quantity.

#### Cart

* `id`.
* `user_id`.
* `created_at`, `updated_at`.

#### Cart Items

* `id`.
* `cart_id`.
* `product_id`.
* `quantity`.

Enforce one cart-item record per product in a cart.

#### Orders

* `id`.
* `order_number` — unique.
* `user_id`.
* `status`.
* `payment_status`.
* `subtotal`.
* `tax_amount`.
* `shipping_amount`.
* `discount_amount`.
* `total_amount`.
* `shipping_address_snapshot`.
* `created_at`, `updated_at`.

Use decimal-compatible numeric database types for monetary values.

#### Order Items

* `id`.
* `order_id`.
* `product_id` — nullable if a product is deleted or archived under an appropriate retention policy.
* `product_name_snapshot`.
* `unit_price`.
* `quantity`.
* `line_total`.

#### Payments

* `id`.
* `order_id`.
* `provider`.
* `provider_reference`.
* `amount`.
* `status`.
* `created_at`.

Never store raw card numbers, CVVs, or payment-provider secrets in this table.

#### Shop Settings

* `id`.
* `shop_name`.
* `since`.
* `shop_description`.
* `logo_path`.
* `contact_email`.
* `contact_phone`.
* `currency`.
* `shipping_settings`.
* `tax_settings`.

Store legal policy content in versioned records or manage it through a controlled admin interface.

### 4. Relationships

* One user can have multiple addresses and orders.
* One category can contain multiple products.
* One product has one inventory record.
* One cart can contain multiple cart items.
* One order contains multiple order items.
* One order may have multiple payment attempts.
* Inventory movements reference the product and, when relevant, the related order.

### 5. Route Design

#### Public

* `GET /` — home.
* `GET /products` — product listing.
* `GET /products/<slug>` — product details.
* `GET /categories/<slug>` — category listing.
* `GET /terms` — terms and conditions.
* `GET /privacy` — privacy policy.

#### Authentication

* `GET, POST /register`.
* `GET, POST /login`.
* `POST /logout`.
* `GET /account`.
* `GET, POST /account/password`.

#### Shopping

* `GET /cart`.
* `POST /cart/items` — add an item.
* `POST /cart/items/<id>/update`.
* `POST /cart/items/<id>/remove`.
* `GET, POST /checkout`.
* `GET /orders/<order_number>`.

#### Administration

* `GET /admin`.
* `GET, POST /admin/products/new`.
* `GET, POST /admin/products/<id>/edit`.
* `POST /admin/products/<id>/archive`.
* `GET, POST /admin/categories`.
* `GET /admin/inventory`.
* `POST /admin/inventory/adjustments`.
* `GET /admin/orders`.
* `GET /admin/orders/<id>`.
* `POST /admin/orders/<id>/status`.
* `GET, POST /admin/settings`.

Use POST, PUT, PATCH, or DELETE semantics for state-changing operations; do not mutate data through GET requests. All mutation routes require authorization and CSRF protection.

### 6. Checkout and Inventory Flow

1. Customer submits the checkout form.
2. Server validates the address, cart, and requested quantities.
3. Server retrieves current product prices and checks stock.
4. Server calculates subtotal, discounts, shipping, tax, and final total.
5. The application creates a pending order and its item snapshots inside a database transaction.
6. Inventory is reserved or deducted using concurrency-safe database operations.
7. If online payment is enabled, the server creates a payment request with the provider.
8. The server verifies the payment result through a trusted provider response or webhook.
9. The order becomes paid only after successful verification.
10. Failed or expired payments release reserved stock according to the payment and inventory policy.
11. The customer receives an order confirmation.

Use idempotency keys or an equivalent deduplication mechanism for checkout and payment operations.

### 7. Configuration and Environment

Keep secrets and deployment-specific values outside source code.

Example `.env.example`:

FLASK_APP=run.py
FLASK_DEBUG=0
SECRET_KEY=replace-with-a-random-secret
DATABASE_URL=replace-with-database-url

Load configuration through a supported configuration loader. Never commit a real `.env` file, production secret, database credential, or payment key.

### 8. Testing Requirements

* Unit tests for price calculations and inventory services.
* Authentication and authorization tests.
* Product and category CRUD tests.
* Cart quantity and stock-validation tests.
* Checkout transaction and duplicate-request tests.
* Payment webhook signature and idempotency tests if payments are enabled.
* Tests for invalid forms and CSRF protection.
* Tests confirming customers cannot access admin routes.
* Tests for simultaneous orders competing for the last item.
* Migration and backup-restore tests.

### 9. Deployment Requirements

* Use HTTPS.
* Use a production WSGI server.
* Disable debug mode.
* Configure secure cookies and trusted host handling.
* Use a production database with backups.
* Restrict database network access.
* Store uploaded images outside executable code paths.
* Set log rotation, error monitoring, and operational alerts.
* Test database restore procedures before launch.
