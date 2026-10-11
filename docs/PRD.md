# Product Requirements Document (PRD)

## Single-Shop E-commerce Website

### 1. Project Overview

**Project type:** Single-shop online shopping website

**Goal:** Build a secure, responsive website where customers can discover products, add items to a cart, place orders, and view their order status. The shop owner can manage products, categories, stock, and orders through an administrative interface.

**Technology:** Python, Flask, HTML, CSS, JavaScript where required, and a relational database.

### 2. Configurable Shop Information

The website must support configurable shop information instead of hardcoding business details into templates.

| Variable            | Purpose                                    |
| ------------------- | ------------------------------------------ |
| `shop_name`         | Shop name displayed throughout the website |
| `since`             | Year the shop was established              |
| `shop_description`  | Short description of the business          |
| `shop_logo`         | Shop logo                                  |
| `shop_email`        | Official contact email                     |
| `shop_phone`        | Customer support phone                     |
| `shop_address`      | Business address                           |
| `currency`          | Currency used for prices, e.g. INR         |
| `tax_settings`      | Applicable tax configuration               |
| `shipping_settings` | Shipping fees and delivery rules           |

The `shop_name` and `since` values must be editable through configuration or the admin panel.

### 3. User Roles

**Guest**

* Browse the homepage, categories, and products.
* Search and filter products.
* View terms and conditions and privacy policy.
* Register or log in.

**Registered customer**

* Manage profile and delivery addresses.
* Add products to the cart.
* Place orders.
* View order history and order status.
* Cancel eligible orders according to the shop's policy.
* Log out and change passwords.

**Administrator**

* Access a protected admin dashboard.
* Create, update, archive, and manage products.
* Manage categories and product images.
* View and update inventory.
* View orders and update their statuses.
* Manage customer accounts where necessary.
* Configure shop information and policies.
* Review low-stock products and sales summaries.

### 4. Website Pages

#### Public pages

1. **Home page**

   * Shop branding and navigation.
   * Featured products and categories.
   * Search bar.
   * Promotional banners.
   * New arrivals and popular products.
   * Footer containing contact details and legal links.

2. **Items page**

   * Product listing with image, name, price, and stock availability.
   * Search, sorting, and filtering.
   * Pagination.
   * Product detail view.

3. **Category page**

   * Products belonging to a selected category.
   * Category description.
   * Sorting and filtering.

4. **Terms and conditions**

   * Shopping rules.
   * Pricing and order acceptance.
   * Shipping, returns, cancellations, and refunds.
   * Customer responsibilities.

5. **Privacy policy**

   * Information collected.
   * Purpose of data collection.
   * Data retention and deletion.
   * Third-party services and payment providers.
   * Customer privacy rights and contact information.

#### Authentication pages

6. **Register**

   * Name, email, and password.
   * Password confirmation.
   * Server-side validation.
   * Duplicate email prevention.
   * Acceptance of applicable terms.

7. **Login**

   * Email and password.
   * Generic error messages.
   * Session creation.
   * Logout and session invalidation.

8. **Customer account**

   * Profile details.
   * Saved addresses.
   * Order history.
   * Password change.

#### Shopping pages

9. **Cart**

   * Product image, price, quantity, and subtotal.
   * Quantity updates and item removal.
   * Stock availability checks.
   * Total calculation.

10. **Checkout**

    * Delivery address.
    * Order summary.
    * Shipping charges and taxes where applicable.
    * Payment method.
    * Final order confirmation.

11. **Order confirmation and order details**

    * Order number.
    * Purchased products.
    * Final amount.
    * Payment status.
    * Order and delivery status.

#### Administration pages

12. **Admin dashboard**

    * Sales summaries.
    * Total orders and customers.
    * Low-stock alerts.
    * Recent orders.

13. **Inventory management**

    * Current stock levels.
    * Stock additions and reductions.
    * Low-stock threshold.
    * Stock movement history.
    * Prevention of negative stock.

14. **Product management**

    * Add and edit products.
    * Upload product images.
    * Set prices, descriptions, categories, and stock.
    * Activate, deactivate, or archive products.

15. **Category management**

    * Create and edit categories.
    * Assign products.
    * Prevent deletion when referenced products require reassignment.

16. **Order management**

    * View order details.
    * Update fulfillment status.
    * Record cancellations and refunds.
    * Maintain an order-status history.

17. **Shop settings**

    * Edit shop name, establishment year, logo, contact details, shipping settings, and policy content.

### 5. Core Functional Requirements

* Product prices, totals, discounts, and stock must be calculated or validated on the server.
* Customers must not be able to access administrative routes.
* Only available products can be purchased.
* Stock must be checked again during checkout.
* An order must retain a snapshot of product names, quantities, and prices at purchase time.
* Each order must have a unique order number.
* Cart and checkout data must be validated before order creation.
* Order creation, stock deduction, and order-item creation must use a database transaction.
* Repeated checkout requests must not create duplicate orders or charge customers twice.
* Administrators must be able to track changes to inventory and order status.
* The interface must work on desktop, tablet, and mobile screens.

### 6. Non-Functional Requirements

**Security:** Password hashing, access control, CSRF protection, secure sessions, validation, and safe database queries.

**Performance:** Paginated product listings, optimized images, database indexes, and minimal unnecessary requests.

**Usability:** Clear navigation, accessible forms, useful validation messages, and a simple checkout process.

**Reliability:** Database transactions, backups, error logging, and graceful handling of failed payments.

**Maintainability:** Modular Flask application, reusable templates, configuration through environment variables, and automated tests.

### 7. MVP Scope

**Required for the first release**

* Shop branding and configuration.
* Registration, login, logout, and customer accounts.
* Product and category browsing.
* Cart and checkout.
* Inventory management.
* Admin dashboard and order management.
* Terms and conditions and privacy policy.
* Essential security controls and tests.

**Optional future enhancements**

* Product reviews and ratings.
* Wishlist.
* Coupons and discount codes.
* Email or SMS notifications.
* Advanced sales reports.
* Product recommendations.
* Delivery tracking integration.

### 8. Success Criteria

* Customers can complete the shopping flow without assistance.
* Unauthorized users cannot access admin operations.
* Stock cannot become negative through concurrent or repeated orders.
* Order totals match server-side calculations.
* Passwords are never stored in plaintext.
* Critical user flows pass automated tests.
* The website works on supported mobile and desktop browsers.

### 9. Open Business Decisions

* Product type and expected catalog size.
* Cash on delivery, online payment, or both.
* Shipping providers and delivery regions.
* Return, cancellation, and refund rules.
* Tax and invoice requirements.
* Whether customer accounts are mandatory for checkout.
