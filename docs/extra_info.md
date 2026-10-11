# Finalized Project Specification

# Single-Shop E-commerce Website

PRD + TRD + Security Guide + Development Roadmap

Backend

Python + Flask

Database

SQLite

Payments

Cash on Delivery (COD)

Deployment

Cloud hosting

## 1. Final business rules

* Single shop: One business owns and manages the complete catalog.

* Branding: `shop_name` and `since` are configurable, along with contact details, logo, and other shop settings.

* Currency: INR (₹) throughout the website.

* Checkout: Customers must register and log in before placing orders.

* Payment: Cash on Delivery only. No online payment gateway is required for version 1.

* Shipping: The shop owner manually manages delivery and updates order statuses.

* Inventory: Stock is managed by the administrator and updated safely when orders are placed or cancelled.

* Administration: Only authorized administrators can manage products, inventory, categories, orders, and settings.

Important technical decision: SQLite is suitable for development and a small, low-traffic deployment when used on persistent storage with proper backups. Because this is a cloud-hosted store, the application must use a persistent disk, a single-writer deployment strategy, and tested backup and restore procedures. If the hosting platform has ephemeral storage or the store grows to require multiple application instances, migrate to PostgreSQL.

## 2. Final PRD — Product Requirements Document

### User roles and permissions

| Feature                        | Guest | Customer | Admin |
| ------------------------------ | ----- | -------- | ----- |
| Browse products and categories | Yes   | Yes      | Yes   |
| Register and log in            | Yes   | Yes      | Yes   |
| Manage personal account        | No    | Yes      | Yes   |
| Manage cart                    | No    | Yes      | Yes   |
| Place COD orders               | No    | Yes      | Yes   |
| View own order history         | No    | Yes      | Yes   |
| Manage products and categories | No    | No       | Yes   |
| Adjust inventory               | No    | No       | Yes   |
| Manage all orders              | No    | No       | Yes   |
| Change shop settings           | No    | No       | Yes   |

Admin access should be a separate role, not a public registration option. The first administrator must be created using a secure CLI command or one-time setup process.

### Required pages

![Ecommerce Storefront Platform — Online · Built with Blink](https://images.openai.com/static-rsc-4/SNGVIosYCY8nKDfu1rk73kFX09EBoyYSPc600gAeVF29oi-2FPOBzc64hWYhy4BW7bjA9N2vD7zGIQ7H_UdSdhQeEMDoLLS6Y8x8BbYzYzXlvfaZ3tZ8r4SdjwZ2bDNZcHilIpUBEE8F11wHN2dmPbE9rzn425Q_TJFlP07XP7U?purpose=inline)

Add to Favorites

Customer storefront

Home, products, product details, categories, search, cart, checkout, order confirmation, account, order history, login, registration, terms, privacy.

![Sales Management - Inventory Dashboard by Fixoria Studio on Dribbble](https://images.openai.com/static-rsc-4/ioXYWXL9T92gO8KPtLyHpK4gwyDNwgQwgx6xVIOUk6Xc7BuzgikcivpeTGIT9fOPZGHngjOEqYJYLZxR41tOaXetIabHXX5To1UeuPM6L0Jhd-EtukWYU_mZnHvxUZKJTxHvZrJq-vtF-hJbDwrrt_FTPU_pNIxgrqplWnswHMk?purpose=inline)

Add to Favorites

Admin panel

Dashboard, product CRUD, category CRUD, inventory, stock movement history, orders, customer management, shop settings, policy content.

### Core workflows

Shopping workflow

1. Customer browses products and selects quantities.

2. Customer logs in or registers.

3. Customer adds products to a persistent cart.

4. Customer enters or selects a delivery address.

5. Server verifies product availability and recalculates the order total.

6. Customer confirms a COD order.

7. The system creates the order and updates stock within a database transaction.

8. The customer receives an order confirmation with a unique order number.

Admin workflow

1. Admin logs in.

2. Admin creates or updates products and categories.

3. Admin adjusts stock with a reason for each manual adjustment.

4. Admin reviews incoming COD orders.

5. Admin updates fulfillment status as orders are confirmed, packed, shipped, delivered, or cancelled.

6. Admin reviews low-stock alerts and inventory history.

### Order statuses

Use a controlled set of statuses:

* `PLACED`

* `CONFIRMED`

* `PACKED`

* `SHIPPED`

* `DELIVERED`

* `CANCELLED`

Track COD collection separately using a `cod_payment_status` field, such as `PENDING`, `COLLECTED`, or `FAILED`. An order being delivered does not automatically prove that payment was collected.

### Acceptance criteria

* Customers cannot place orders for inactive products or unavailable stock.

* A customer's order and address information cannot be viewed or changed by another customer.

* Order totals are calculated on the server in INR.

* A successful order reduces stock exactly once.

* Cancelling an eligible order restores stock exactly once.

* Repeated submissions cannot duplicate an order or stock adjustment.

* Only admins can access inventory, product-management, and order-management operations.

* Shop branding and `since` are editable without modifying HTML templates.

* Legal pages are accessible without authentication.

* Core workflows pass automated tests before deployment.

## 3. Final TRD — Technical Requirements Document

### Recommended architecture

Use Flask's application factory and Blueprints to keep the project modular.

Diagram options

![](data\:image/svg+xml;utf8,%3Csvg%20id%3D%22mermaid-_r_b2_%22%20width%3D%22744.4347534179688%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20class%3D%22flowchart%22%20height%3D%22541.9747314453125%22%20viewBox%3D%224%204%20744.4347534179688%20541.9747314453125%22%20role%3D%22graphics-document%20document%22%20aria-roledescription%3D%22flowchart-v2%22%3E%3Cstyle%3E%23mermaid-_r_b2_%7Bfont-family%3A%22-apple-system%22%2C%22BlinkMacSystemFont%22%2C%22Segoe%20UI%22%2C%22Roboto%22%2C%22Oxygen%22%2C%22Ubuntu%22%2C%22Cantarell%22%2C%22Helvetica%20Neue%22%2C%22Arial%22%2C%22sans-serif%22%3Bfont-size%3A14px%3Bfill%3Argb\(255%2C%20255%2C%20255\)%3B%7D%40keyframes%20edge-animation-frame%7Bfrom%7Bstroke-dashoffset%3A0%3B%7D%7D%40keyframes%20dash%7Bto%7Bstroke-dashoffset%3A0%3B%7D%7D%23mermaid-_r_b2_%20.edge-animation-slow%7Bstroke-dasharray%3A9%2C5!important%3Bstroke-dashoffset%3A900%3Banimation%3Adash%2050s%20linear%20infinite%3Bstroke-linecap%3Around%3B%7D%23mermaid-_r_b2_%20.edge-animation-fast%7Bstroke-dasharray%3A9%2C5!important%3Bstroke-dashoffset%3A900%3Banimation%3Adash%2020s%20linear%20infinite%3Bstroke-linecap%3Around%3B%7D%23mermaid-_r_b2_%20.error-icon%7Bfill%3Argb\(33%2C%2033%2C%2033\)%3B%7D%23mermaid-_r_b2_%20.error-text%7Bfill%3Argb\(255%2C%20255%2C%20255\)%3Bstroke%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20.edge-thickness-normal%7Bstroke-width%3A1px%3B%7D%23mermaid-_r_b2_%20.edge-thickness-thick%7Bstroke-width%3A3.5px%3B%7D%23mermaid-_r_b2_%20.edge-pattern-solid%7Bstroke-dasharray%3A0%3B%7D%23mermaid-_r_b2_%20.edge-thickness-invisible%7Bstroke-width%3A0%3Bfill%3Anone%3B%7D%23mermaid-_r_b2_%20.edge-pattern-dashed%7Bstroke-dasharray%3A3%3B%7D%23mermaid-_r_b2_%20.edge-pattern-dotted%7Bstroke-dasharray%3A2%3B%7D%23mermaid-_r_b2_%20.marker%7Bfill%3Argb\(205%2C%20205%2C%20205\)%3Bstroke%3Argb\(205%2C%20205%2C%20205\)%3B%7D%23mermaid-_r_b2_%20.marker.cross%7Bstroke%3Argb\(205%2C%20205%2C%20205\)%3B%7D%23mermaid-_r_b2_%20svg%7Bfont-family%3A%22-apple-system%22%2C%22BlinkMacSystemFont%22%2C%22Segoe%20UI%22%2C%22Roboto%22%2C%22Oxygen%22%2C%22Ubuntu%22%2C%22Cantarell%22%2C%22Helvetica%20Neue%22%2C%22Arial%22%2C%22sans-serif%22%3Bfont-size%3A14px%3B%7D%23mermaid-_r_b2_%20p%7Bmargin%3A0%3B%7D%23mermaid-_r_b2_%20.label%7Bfont-family%3A%22-apple-system%22%2C%22BlinkMacSystemFont%22%2C%22Segoe%20UI%22%2C%22Roboto%22%2C%22Oxygen%22%2C%22Ubuntu%22%2C%22Cantarell%22%2C%22Helvetica%20Neue%22%2C%22Arial%22%2C%22sans-serif%22%3Bcolor%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20.cluster-label%20text%7Bfill%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20.cluster-label%20span%7Bcolor%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20.cluster-label%20span%20p%7Bbackground-color%3Atransparent%3B%7D%23mermaid-_r_b2_%20.label%20text%2C%23mermaid-_r_b2_%20span%7Bfill%3Argb\(255%2C%20255%2C%20255\)%3Bcolor%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20.node%20rect%2C%23mermaid-_r_b2_%20.node%20circle%2C%23mermaid-_r_b2_%20.node%20ellipse%2C%23mermaid-_r_b2_%20.node%20polygon%2C%23mermaid-_r_b2_%20.node%20path%7Bfill%3Argb\(9%2C%2023%2C%2044\)%3Bstroke%3Argb\(31%2C%2078%2C%20148\)%3Bstroke-width%3A1px%3B%7D%23mermaid-_r_b2_%20.rough-node%20.label%20text%2C%23mermaid-_r_b2_%20.node%20.label%20text%2C%23mermaid-_r_b2_%20.image-shape%20.label%2C%23mermaid-_r_b2_%20.icon-shape%20.label%7Btext-anchor%3Amiddle%3B%7D%23mermaid-_r_b2_%20.node%20.katex%20path%7Bfill%3A%23000%3Bstroke%3A%23000%3Bstroke-width%3A1px%3B%7D%23mermaid-_r_b2_%20.rough-node%20.label%2C%23mermaid-_r_b2_%20.node%20.label%2C%23mermaid-_r_b2_%20.image-shape%20.label%2C%23mermaid-_r_b2_%20.icon-shape%20.label%7Btext-align%3Acenter%3B%7D%23mermaid-_r_b2_%20.node.clickable%7Bcursor%3Apointer%3B%7D%23mermaid-_r_b2_%20.root%20.anchor%20path%7Bfill%3Argb\(205%2C%20205%2C%20205\)!important%3Bstroke-width%3A0%3Bstroke%3Argb\(205%2C%20205%2C%20205\)%3B%7D%23mermaid-_r_b2_%20.arrowheadPath%7Bfill%3Argb\(205%2C%20205%2C%20205\)%3B%7D%23mermaid-_r_b2_%20.edgePath%20.path%7Bstroke%3Argb\(205%2C%20205%2C%20205\)%3Bstroke-width%3A2.0px%3B%7D%23mermaid-_r_b2_%20.flowchart-link%7Bstroke%3Argb\(205%2C%20205%2C%20205\)%3Bfill%3Anone%3B%7D%23mermaid-_r_b2_%20.edgeLabel%7Bbackground-color%3Argb\(0%2C%200%2C%200\)%3Btext-align%3Acenter%3B%7D%23mermaid-_r_b2_%20.edgeLabel%20p%7Bbackground-color%3Argb\(0%2C%200%2C%200\)%3B%7D%23mermaid-_r_b2_%20.edgeLabel%20rect%7Bopacity%3A0.5%3Bbackground-color%3Argb\(0%2C%200%2C%200\)%3Bfill%3Argb\(0%2C%200%2C%200\)%3B%7D%23mermaid-_r_b2_%20.labelBkg%7Bbackground-color%3Argba\(0%2C%200%2C%200%2C%200.5\)%3B%7D%23mermaid-_r_b2_%20.cluster%20rect%7Bfill%3Argb\(33%2C%2033%2C%2033\)%3Bstroke%3Argba\(255%2C%20255%2C%20255%2C%200.05\)%3Bstroke-width%3A1px%3B%7D%23mermaid-_r_b2_%20.cluster%20text%7Bfill%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20.cluster%20span%7Bcolor%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20div.mermaidTooltip%7Bposition%3Aabsolute%3Btext-align%3Acenter%3Bmax-width%3A200px%3Bpadding%3A2px%3Bfont-family%3A%22-apple-system%22%2C%22BlinkMacSystemFont%22%2C%22Segoe%20UI%22%2C%22Roboto%22%2C%22Oxygen%22%2C%22Ubuntu%22%2C%22Cantarell%22%2C%22Helvetica%20Neue%22%2C%22Arial%22%2C%22sans-serif%22%3Bfont-size%3A12px%3Bbackground%3Argb\(33%2C%2033%2C%2033\)%3Bborder%3A1px%20solid%20rgba\(255%2C%20255%2C%20255%2C%200.05\)%3Bborder-radius%3A2px%3Bpointer-events%3Anone%3Bz-index%3A100%3B%7D%23mermaid-_r_b2_%20.flowchartTitleText%7Btext-anchor%3Amiddle%3Bfont-size%3A18px%3Bfill%3Argb\(255%2C%20255%2C%20255\)%3B%7D%23mermaid-_r_b2_%20rect.text%7Bfill%3Anone%3Bstroke-width%3A0%3B%7D%23mermaid-_r_b2_%20.icon-shape%2C%23mermaid-_r_b2_%20.image-shape%7Bbackground-color%3Argb\(0%2C%200%2C%200\)%3Btext-align%3Acenter%3B%7D%23mermaid-_r_b2_%20.icon-shape%20p%2C%23mermaid-_r_b2_%20.image-shape%20p%7Bbackground-color%3Argb\(0%2C%200%2C%200\)%3Bpadding%3A2px%3B%7D%23mermaid-_r_b2_%20.icon-shape%20rect%2C%23mermaid-_r_b2_%20.image-shape%20rect%7Bopacity%3A0.5%3Bbackground-color%3Argb\(0%2C%200%2C%200\)%3Bfill%3Argb\(0%2C%200%2C%200\)%3B%7D%23mermaid-_r_b2_%20.label-icon%7Bdisplay%3Ainline-block%3Bheight%3A1em%3Boverflow%3Avisible%3Bvertical-align%3A-0.125em%3B%7D%23mermaid-_r_b2_%20.node%20.label-icon%20path%7Bfill%3AcurrentColor%3Bstroke%3Arevert%3Bstroke-width%3Arevert%3B%7D%23mermaid-_r_b2_%20.node%20text%7Bfont-size%3A16px%3Bfont-weight%3A600%3Bletter-spacing%3A-0.32px%3Bfill%3A%2399ceff%3B%7D%23mermaid-_r_b2_%20.edgeLabels%20text%7Bfont-size%3A13px%3Bfont-weight%3A600%3Bletter-spacing%3A-0.08px%3Bfill%3A%2399ceff%3B%7D%23mermaid-_r_b2_%20.node%20tspan%5Bfont-weight%3D%22normal%22%5D%2C%23mermaid-_r_b2_%20.edgeLabels%20tspan%5Bfont-weight%3D%22normal%22%5D%7Bfont-weight%3A600%3B%7D%23mermaid-_r_b2_%20.edgeLabel%20.label%20rect%7Bopacity%3A1%3Brx%3A13px%3Bry%3A13px%3Bfill%3A%23000e1a%3Bstroke%3Argb\(26%2C%2062%2C%2095\)%3Bstroke-width%3A1px%3B%7D%23mermaid-_r_b2_%20.node%20rect%2C%23mermaid-_r_b2_%20.node%20circle%2C%23mermaid-_r_b2_%20.node%20ellipse%2C%23mermaid-_r_b2_%20.node%20polygon%2C%23mermaid-_r_b2_%20.node%20path%7Bfill%3Argb\(0%2C%2040%2C%2077\)%3Bstroke%3Argba\(255%2C%20255%2C%20255%2C%200.1\)%3Bstroke-width%3A1px%3B%7D%23mermaid-_r_b2_%20.node%20rect%7Brx%3A16px%3Bry%3A16px%3B%7D%23mermaid-_r_b2_%20.node.mermaid-decision%20.label-container%7Bfill%3A%23000e1a%3Bstroke%3Argb\(26%2C%2062%2C%2095\)%3Bstroke-dasharray%3A2%202%3B%7D%23mermaid-_r_b2_%20.edgePaths%20.flowchart-link%7Bstroke%3Argb\(26%2C%2062%2C%2095\)%3Bstroke-width%3A1px%3Bstroke-linecap%3Around%3Bstroke-linejoin%3Around%3B%7D%23mermaid-_r_b2_%20.marker%7Bfill%3Argb\(26%2C%2062%2C%2095\)%3Bstroke%3Argb\(26%2C%2062%2C%2095\)%3B%7D%23mermaid-_r_b2_%20.node%7Bcolor-scheme%3Adark%3B%7D%23mermaid-_r_b2_%20%3Aroot%7B--mermaid-font-family%3A%22-apple-system%22%2C%22BlinkMacSystemFont%22%2C%22Segoe%20UI%22%2C%22Roboto%22%2C%22Oxygen%22%2C%22Ubuntu%22%2C%22Cantarell%22%2C%22Helvetica%20Neue%22%2C%22Arial%22%2C%22sans-serif%22%3B%7D%3C%2Fstyle%3E%3Cg%3E%3Cmarker%20id%3D%22mermaid-_r_b2__flowchart-v2-pointEnd%22%20class%3D%22marker%20flowchart-v2%22%20viewBox%3D%22-5%20-5%2010%2010%22%20refX%3D%220%22%20refY%3D%220%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2210%22%20markerHeight%3D%2210%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%200%200%20L%204%200%20M%200.8180194846605362%20-3.181980515339464%20L%204%200%20L%200.8180194846605362%203.181980515339464%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%20none%3B%20fill%3A%20none%3B%20stroke-linecap%3A%20round%3B%20stroke-linejoin%3A%20round%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-_r_b2__flowchart-v2-pointStart%22%20class%3D%22marker%20flowchart-v2%22%20viewBox%3D%22-5%20-5%2010%2010%22%20refX%3D%220%22%20refY%3D%220%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2210%22%20markerHeight%3D%2210%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%200%200%20L%20-4%200%20M%20-0.8180194846605362%20-3.181980515339464%20L%20-4%200%20L%20-0.8180194846605362%203.181980515339464%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%20none%3B%20fill%3A%20none%3B%20stroke-linecap%3A%20round%3B%20stroke-linejoin%3A%20round%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-_r_b2__flowchart-v2-circleEnd%22%20class%3D%22marker%20flowchart-v2%22%20viewBox%3D%220%200%2010%2010%22%20refX%3D%2211%22%20refY%3D%225%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Ccircle%20cx%3D%225%22%20cy%3D%225%22%20r%3D%225%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fcircle%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-_r_b2__flowchart-v2-circleStart%22%20class%3D%22marker%20flowchart-v2%22%20viewBox%3D%220%200%2010%2010%22%20refX%3D%22-1%22%20refY%3D%225%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Ccircle%20cx%3D%225%22%20cy%3D%225%22%20r%3D%225%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%201%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fcircle%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-_r_b2__flowchart-v2-crossEnd%22%20class%3D%22marker%20cross%20flowchart-v2%22%20viewBox%3D%220%200%2011%2011%22%20refX%3D%2212%22%20refY%3D%225.2%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%201%2C1%20l%209%2C9%20M%2010%2C1%20l%20-9%2C9%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%202%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3Cmarker%20id%3D%22mermaid-_r_b2__flowchart-v2-crossStart%22%20class%3D%22marker%20cross%20flowchart-v2%22%20viewBox%3D%220%200%2011%2011%22%20refX%3D%22-1%22%20refY%3D%225.2%22%20markerUnits%3D%22userSpaceOnUse%22%20markerWidth%3D%2211%22%20markerHeight%3D%2211%22%20orient%3D%22auto%22%3E%3Cpath%20d%3D%22M%201%2C1%20l%209%2C9%20M%2010%2C1%20l%20-9%2C9%22%20class%3D%22arrowMarkerPath%22%20style%3D%22stroke-width%3A%202%3B%20stroke-dasharray%3A%201%2C%200%3B%22%3E%3C%2Fpath%3E%3C%2Fmarker%3E%3C%2Fg%3E%3Cg%20class%3D%22subgraphs%22%3E%3C%2Fg%3E%3Cg%20class%3D%22nodes%22%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-A-0%22%20transform%3D%22translate\(323.7307586669922%2C%2047.29999923706055\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-108.19985961914062%22%20y%3D%22-35.29999923706055%22%20width%3D%22216.39971923828125%22%20height%3D%2270.5999984741211%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-19.299999237060547\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EBrowser%3A%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20HTML%2C%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20CSS%2C%3C%2Ftspan%3E%3C%2Ftspan%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%221em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EJavaScript%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-B-1%22%20transform%3D%22translate\(541.0812861124674%2C%20152.5999984741211\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-131.57191467285156%22%20y%3D%22-30%22%20width%3D%22263.1438293457031%22%20height%3D%2260%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-10.5\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EFlask%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Routes%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20and%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Blueprints%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-C-3%22%20transform%3D%22translate\(345.5584030151367%2C%20257.89999771118164\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-103.3359375%22%20y%3D%22-35.29999923706055%22%20width%3D%22206.671875%22%20height%3D%2270.5999984741211%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-19.299999237060547\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EAuthentication%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20and%3C%2Ftspan%3E%3C%2Ftspan%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%221em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EAuthorization%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-D-5%22%20transform%3D%22translate\(584.938591003418%2C%20260.5499973297119\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-96.04425048828125%22%20y%3D%22-30%22%20width%3D%22192.0885009765625%22%20height%3D%2260%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-10.5\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EBusiness%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Services%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-E-7%22%20transform%3D%22translate\(112.1875%2C%20388.49999618530273\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-100.1875%22%20y%3D%22-30%22%20width%3D%22200.375%22%20height%3D%2260%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-10.5\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3ESQLAlchemy%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20ORM%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-F-9%22%20transform%3D%22translate\(611.3639348347981%2C%20500.88736724853516\)%22%3E%3Cpath%20d%3D%22M0%2C12.72491339111255%20a64.79034423828125%2C12.72491339111255%200%2C0%2C0%20129.5806884765625%2C0%20a64.79034423828125%2C12.72491339111255%200%2C0%2C0%20-129.5806884765625%2C0%20l0%2C48.72491339111255%20a64.79034423828125%2C12.72491339111255%200%2C0%2C0%20129.5806884765625%2C0%20l0%2C-48.72491339111255%22%20class%3D%22basic%20label-container%22%20style%3D%22%22%20transform%3D%22translate\(-64.79034423828125%2C%20-37.08737008666883\)%22%3E%3C%2Fpath%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(-0.40753173828125%2C%200.5\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3ESQLite%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Database%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-G-11%22%20transform%3D%22translate\(368.9308090209961%2C%20383.1999969482422\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-116.5558090209961%22%20y%3D%22-30%22%20width%3D%22233.1116180419922%22%20height%3D%2260%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-10.5\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EProduct%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Image%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Storage%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-H-13%22%20transform%3D%22translate\(632.9607162475586%2C%20388.49999618530273\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-107.4740982055664%22%20y%3D%22-35.29999923706055%22%20width%3D%22214.9481964111328%22%20height%3D%2270.5999984741211%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-19.299999237060547\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EOrder%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20and%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Inventory%3C%2Ftspan%3E%3C%2Ftspan%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%221em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EServices%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22node%20default%22%20id%3D%22flowchart-I-16%22%20transform%3D%22translate\(584.938591003418%2C%2047.29999923706055\)%22%3E%3Crect%20class%3D%22basic%20label-container%22%20style%3D%22%22%20x%3D%22-113.00797271728516%22%20y%3D%22-35.29999923706055%22%20width%3D%22226.0159454345703%22%20height%3D%2270.5999984741211%22%3E%3C%2Frect%3E%3Cg%20class%3D%22label%22%20style%3D%22%22%20transform%3D%22translate\(0%2C%20-19.299999237060547\)%22%3E%3Crect%3E%3C%2Frect%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3Ctext%20y%3D%22-10.1%22%20style%3D%22%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3ECloud%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Reverse%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20Proxy%3C%2Ftspan%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3E%20%2F%3C%2Ftspan%3E%3C%2Ftspan%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%221em%22%20dy%3D%221.1em%22%3E%3Ctspan%20font-style%3D%22normal%22%20class%3D%22text-inner-tspan%22%20font-weight%3D%22normal%22%3EHTTPS%3C%2Ftspan%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edges%20edgePaths%22%3E%3Cpath%20d%3D%22M323.7307586669922%2C82.5999984741211L323.7307586669922%2C95.81704244882644Q323.7307586669922%2C97.5999984741211%20324.8165451046191%2C99.01421203649419L324.8165451046191%2C99.01421203649419Q325.902331542246%2C100.42842559886728%20327.3165451046191%2C101.51421203649417L327.3165451046191%2C101.51421203649419Q328.7307586669922%2C102.5999984741211%20330.51371469228684%2C102.5999984741211L490.44102519622226%2C102.5999984741211Q492.2239812215169%2C102.5999984741211%20493.63819478389%2C103.685784911748L493.63819478389%2C103.68578491174802Q495.0524083462631%2C104.77157134937491%20496.13819478389%2C106.185784911748L496.13819478389%2C106.185784911748Q497.2239812215169%2C107.5999984741211%20497.2239812215169%2C109.38295449941575L497.2239812215169%2C112.5999984741211%22%20id%3D%22L_A_B_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_A_B_0%22%20data-points%3D%22W3sieCI6MzIzLjczMDc1ODY2Njk5MjIsInkiOjgyLjU5OTk5ODQ3NDEyMTF9LHsieCI6MzIzLjczMDc1ODY2Njk5MjIsInkiOjEwMi41OTk5OTg0NzQxMjExfSx7IngiOjQ5Ny4yMjM5ODEyMjE1MTY5LCJ5IjoxMDIuNTk5OTk4NDc0MTIxMX0seyJ4Ijo0OTcuMjIzOTgxMjIxNTE2OSwieSI6MTE2LjU5OTk5ODQ3NDEyMTF9XQ%3D%3D%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M497.22398122151696%2C182.5999984741211L497.2239812215169%2C195.52893066225562Q497.2239812215169%2C202.5999984741211%20490.15291340965143%2C202.5999984741211L352.34135904043137%2C202.5999984741211Q350.5584030151367%2C202.5999984741211%20349.1441894527636%2C203.685784911748L349.1441894527636%2C203.68578491174802Q347.7299758903905%2C204.7715713493749%20346.6441894527636%2C206.185784911748L346.6441894527636%2C206.185784911748Q345.5584030151367%2C207.5999984741211%20345.5584030151367%2C209.38295449941575L345.5584030151367%2C212.5999984741211%22%20id%3D%22L_B_C_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_B_C_0%22%20data-points%3D%22W3sieCI6NDk3LjIyMzk4MTIyMTUxNjk2LCJ5IjoxODIuNTk5OTk4NDc0MTIxMX0seyJ4Ijo0OTcuMjIzOTgxMjIxNTE2OSwieSI6MjAyLjU5OTk5ODQ3NDEyMTF9LHsieCI6MzQ1LjU1ODQwMzAxNTEzNjcsInkiOjIwMi41OTk5OTg0NzQxMjExfSx7IngiOjM0NS41NTg0MDMwMTUxMzY3LCJ5IjoyMTYuNTk5OTk4NDc0MTIxMX1d%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M584.938591003418%2C182.5999984741211L584.938591003418%2C218.5499973297119%22%20id%3D%22L_B_D_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_B_D_0%22%20data-points%3D%22W3sieCI6NTg0LjkzODU5MTAwMzQxOCwieSI6MTgyLjU5OTk5ODQ3NDEyMTF9LHsieCI6NTg0LjkzODU5MTAwMzQxOCwieSI6MjIyLjU0OTk5NzMyOTcxMTl9XQ%3D%3D%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M536.9164657592773%2C290.5499973297119L536.9164657592773%2C306.41704092294754Q536.9164657592773%2C308.1999969482422%20535.8306793216505%2C309.6142105106153L535.8306793216505%2C309.6142105106153Q534.7448928840236%2C311.0284240729884%20533.3306793216505%2C312.1142105106153L533.3306793216505%2C312.1142105106153Q531.9164657592773%2C313.1999969482422%20530.1335097339827%2C313.1999969482422L118.97045602529465%2C313.1999969482422Q117.1875%2C313.1999969482422%20115.77328643762691%2C314.2857833858691L115.77328643762691%2C314.2857833858691Q114.35907287525382%2C315.371569823496%20113.27328643762692%2C316.7857833858691L113.27328643762691%2C316.7857833858691Q112.1875%2C318.1999969482422%20112.1875%2C319.98295297353684L112.1875%2C346.49999618530273%22%20id%3D%22L_D_E_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_D_E_0%22%20data-points%3D%22W3sieCI6NTM2LjkxNjQ2NTc1OTI3NzMsInkiOjI5MC41NDk5OTczMjk3MTE5fSx7IngiOjUzNi45MTY0NjU3NTkyNzczLCJ5IjozMTMuMTk5OTk2OTQ4MjQyMn0seyJ4IjoxMTIuMTg3NSwieSI6MzEzLjE5OTk5Njk0ODI0MjJ9LHsieCI6MTEyLjE4NzUsInkiOjM1MC40OTk5OTYxODUzMDI3M31d%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M112.1875%2C418.49999618530273L112.1875%2C437.01703939706863Q112.1875%2C438.7999954223633%20113.27328643762691%2C440.2142089847364L113.27328643762692%2C440.2142089847364Q114.35907287525382%2C441.6284225471095%20115.77328643762691%2C442.7142089847364L115.77328643762691%2C442.7142089847364Q117.1875%2C443.7999954223633%20118.97045602529465%2C443.7999954223633L582.9841973967431%2C443.7999954223633Q584.7671534220377%2C443.7999954223633%20586.1813669844108%2C444.8857818599902L586.1813669844108%2C444.8857818599902Q587.5955805467839%2C445.97156829761707%20588.6813669844108%2C447.3857818599902L588.6813669844108%2C447.3857818599902Q589.7671534220377%2C448.7999954223633%20589.7671534220377%2C450.58295144765793L589.7671534220377%2C453.7999954223633%22%20id%3D%22L_E_F_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_E_F_0%22%20data-points%3D%22W3sieCI6MTEyLjE4NzUsInkiOjQxOC40OTk5OTYxODUzMDI3M30seyJ4IjoxMTIuMTg3NSwieSI6NDQzLjc5OTk5NTQyMjM2MzN9LHsieCI6NTg5Ljc2NzE1MzQyMjAzNzcsInkiOjQ0My43OTk5OTU0MjIzNjMzfSx7IngiOjU4OS43NjcxNTM0MjIwMzc3LCJ5Ijo0NTcuNzk5OTk1NDIyMzYzM31d%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M584.938591003418%2C290.5499973297119L584.938591003418%2C326.41704092294754Q584.938591003418%2C328.1999969482422%20583.8528045657911%2C329.6142105106153L583.8528045657911%2C329.6142105106153Q582.7670181281642%2C331.0284240729884%20581.3528045657911%2C332.1142105106153L581.3528045657911%2C332.1142105106153Q579.938591003418%2C333.1999969482422%20578.1556349781233%2C333.1999969482422L375.71376504629075%2C333.1999969482422Q373.9308090209961%2C333.1999969482422%20372.516595458623%2C334.2857833858691L372.516595458623%2C334.2857833858691Q371.1023818962499%2C335.371569823496%20370.016595458623%2C336.7857833858691L370.016595458623%2C336.7857833858691Q368.9308090209961%2C338.1999969482422%20368.9308090209961%2C339.98295297353684L368.9308090209961%2C343.1999969482422%22%20id%3D%22L_D_G_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_D_G_0%22%20data-points%3D%22W3sieCI6NTg0LjkzODU5MTAwMzQxOCwieSI6MjkwLjU0OTk5NzMyOTcxMTl9LHsieCI6NTg0LjkzODU5MTAwMzQxOCwieSI6MzMzLjE5OTk5Njk0ODI0MjJ9LHsieCI6MzY4LjkzMDgwOTAyMDk5NjEsInkiOjMzMy4xOTk5OTY5NDgyNDIyfSx7IngiOjM2OC45MzA4MDkwMjA5OTYxLCJ5IjozNDcuMTk5OTk2OTQ4MjQyMn1d%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M632.9607162475586%2C290.5499973297119L632.9607162475586%2C341.1999969482422%22%20id%3D%22L_D_H_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_D_H_0%22%20data-points%3D%22W3sieCI6NjMyLjk2MDcxNjI0NzU1ODYsInkiOjI5MC41NDk5OTczMjk3MTE5fSx7IngiOjYzMi45NjA3MTYyNDc1NTg2LCJ5IjozNDUuMTk5OTk2OTQ4MjQyMn1d%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M632.9607162475586%2C423.7999954223633L632.9607162475586%2C451.7999954223633%22%20id%3D%22L_H_F_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_H_F_0%22%20data-points%3D%22W3sieCI6NjMyLjk2MDcxNjI0NzU1ODYsInkiOjQyMy43OTk5OTU0MjIzNjMzfSx7IngiOjYzMi45NjA3MTYyNDc1NTg2LCJ5Ijo0NTUuNzk5OTk1NDIyMzYzM31d%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M584.938591003418%2C82.5999984741211L584.938591003418%2C110.5999984741211%22%20id%3D%22L_I_B_0%22%20class%3D%22edge-thickness-normal%20edge-pattern-solid%20edge-thickness-normal%20edge-pattern-solid%20flowchart-link%22%20style%3D%22%3B%22%20data-edge%3D%22true%22%20data-et%3D%22edge%22%20data-id%3D%22L_I_B_0%22%20data-points%3D%22W3sieCI6NTg0LjkzODU5MTAwMzQxOCwieSI6ODIuNTk5OTk4NDc0MTIxMX0seyJ4Ijo1ODQuOTM4NTkxMDAzNDE4LCJ5IjoxMTQuNTk5OTk4NDc0MTIxMX1d%22%20marker-end%3D%22url\(%23mermaid-_r_b2__flowchart-v2-pointEnd\)%22%3E%3C%2Fpath%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabels%22%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%3E%3Crect%20class%3D%22background%22%20style%3D%22stroke%3A%20none%22%3E%3C%2Frect%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_A_B_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_B_C_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_B_D_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_D_E_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_E_F_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_D_G_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_D_H_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_H_F_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3Cg%20class%3D%22edgeLabel%22%3E%3Cg%20class%3D%22label%22%20data-id%3D%22L_I_B_0%22%20transform%3D%22translate\(0%2C%200\)%22%3E%3Ctext%20y%3D%22-10.1%22%3E%3Ctspan%20class%3D%22text-outer-tspan%22%20x%3D%220%22%20y%3D%22-0.1em%22%20dy%3D%221.1em%22%3E%3C%2Ftspan%3E%3C%2Ftext%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E)

### Project structure

```
shop/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── user.py
│   │   ├── address.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   └── shop_settings.py
│   ├── blueprints/
│   │   ├── auth/
│   │   ├── main/
│   │   ├── products/
│   │   ├── cart/
│   │   ├── checkout/
│   │   ├── account/
│   │   └── admin/
│   ├── services/
│   │   ├── pricing.py
│   │   ├── inventory.py
│   │   └── orders.py
│   ├── templates/
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
├── migrations/
├── tests/
├── instance/
├── .env.example
├── .gitignore
├── requirements.txt
└── run.py
```

### Data model

| Model               | Key fields and constraints                                                     |
| ------------------- | ------------------------------------------------------------------------------ |
| `User`              | ID, name, unique normalized email, password hash, role, active flag            |
| `Address`           | User ID, recipient, phone, address lines, city, state, PIN code                |
| `Category`          | Name, unique slug, description, active flag                                    |
| `Product`           | Name, unique slug, description, category, price in INR, active flag            |
| `Inventory`         | Product ID, available quantity, low-stock threshold                            |
| `InventoryMovement` | Product ID, signed quantity change, reason, actor, order reference, timestamp  |
| `Cart`              | User ID, created and updated timestamps                                        |
| `CartItem`          | Cart ID, product ID, quantity; unique cart/product pair                        |
| `Order`             | Unique order number, user ID, status, COD status, totals, address snapshot     |
| `OrderItem`         | Order ID, product name snapshot, unit price, quantity, line total              |
| `ShopSettings`      | Shop name, establishment year, logo, contact details, currency, shipping rules |

Additional constraints:

* Use `Decimal` in Python and `NUMERIC`/decimal-compatible storage for prices. Do not use floating-point arithmetic for money.

* Store all monetary amounts as INR values with two decimal places.

* Use foreign keys, unique constraints, non-negative quantity checks, and database indexes.

* Enable SQLite foreign-key enforcement on every database connection.

* Preserve historical order item names and prices even if a product changes later.

* Use explicit timestamps and record who performed administrative changes.

* Use a database migration tool instead of manually changing production tables.

### Route specification

| Blueprint  | Routes                                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------------------------- |
| `main`     | `GET /`, `GET /terms`, `GET /privacy`                                                                      |
| `auth`     | `GET/POST /register`, `GET/POST /login`, `POST /logout`                                                    |
| `products` | `GET /products`, `GET /products/<slug>`, `GET /categories/<slug>`                                          |
| `cart`     | `GET /cart`, `POST /cart/items`, `POST /cart/items/<id>/update`, `POST /cart/items/<id>/remove`            |
| `checkout` | `GET/POST /checkout`                                                                                       |
| `account`  | `GET /account`, `GET/POST /account/addresses`, `GET /account/orders`, `GET /account/orders/<order_number>` |
| `admin`    | Dashboard, product/category CRUD, inventory adjustments, order management, settings                        |

Use POST requests for actions that change state. A customer must be authenticated before checkout and order-history access. Every admin endpoint must independently enforce admin authorization.

### COD order processing

Use a database transaction to prevent partial updates.

Python

Run

```
# Pseudocode: implement in app/services/orders.py

def place_cod_order(user, cart, address):
    validate_customer(user)
    validate_address_ownership(address, user)

    with database_transaction():
        # Read current products and stock from the database.
        # Verify that every product is active and available.
        # Recalculate all prices, shipping, and totals on the server.
        # Deduct stock using concurrency-safe conditional updates.
        # Create the order and immutable order-item snapshots.
        # Record inventory movements and clear the purchased cart items.
        # Ensure the request cannot create a duplicate order.

        return created_order
```

This is deliberately pseudocode, not a complete implementation. For SQLite, use short transactions, conditional stock updates, a unique idempotency key or equivalent order-request deduplication, and appropriate busy-timeout handling. Do not rely on an in-memory lock, because it does not coordinate multiple worker processes.

### COD and manual shipping rules

* Payment method is fixed to COD for the first release.

* Store the payment method on the order so future changes do not alter historical orders.

* Initial payment status is `PENDING`.

* Mark payment as `COLLECTED` only after the shop confirms receipt of cash.

* Admin-only actions change shipping status.

* Store a timestamp and actor for each status change.

* Reject invalid transitions, such as moving a cancelled order to shipped.

* Define when cancellation is permitted and whether it triggers stock restoration.

* Configure a flat shipping fee or a defined manual shipping rule before launch. Never silently omit shipping from the final total.

## 4. Final Security Guide

### Required security controls

| Risk                       | Required protection                                            |
| -------------------------- | -------------------------------------------------------------- |
| Password theft             | Werkzeug password hashing using a suitable supported algorithm |
| Unauthorized admin access  | Server-side role checks on every admin endpoint                |
| Cross-site request forgery | Flask-WTF CSRF protection                                      |
| SQL injection              | SQLAlchemy parameterized queries and ORM                       |
| Cross-site scripting       | Jinja autoescaping; sanitize rich text if supported            |
| Session theft              | HTTPS, secure cookies, session invalidation                    |
| Account brute force        | Rate limiting and generic login errors                         |
| Fake order totals          | Server-side pricing and shipping calculations                  |
| Stock manipulation         | Transactional, conditional inventory updates                   |
| Duplicate orders           | Idempotency and database uniqueness constraints                |
| Malicious image uploads    | Content validation, size limits, safe filenames                |
| Data loss                  | Persistent storage, backups, tested recovery                   |
| Secret leakage             | Environment-based configuration; no committed secrets          |

### Authentication and authorization

* Hash passwords using a maintained password-hashing implementation. Never store plaintext or reversible password encryption.

* Normalize email addresses consistently and enforce uniqueness in the database.

* Set every public registration to `customer`; never accept the requested role from the browser.

* Create the first administrator through a protected CLI command.

* Use Flask-Login for authentication and explicit server-side role checks for authorization.

* Require CSRF tokens for all state-changing browser forms.

* Rate-limit login, registration, and password-reset endpoints.

* Require reauthentication for sensitive account changes and consider multi-factor authentication for administrators.

### Flask production configuration

Use production-specific configuration rather than relying on framework defaults.

Python

Run

```
import os
from datetime import timedelta

class ProductionConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    WTF_CSRF_ENABLED = True
    DEBUG = False
    TESTING = False
```

This is a configuration example, not the complete application. Set `DATABASE_URL` to the SQLite database file on the host's persistent disk. Validate configuration at startup, and never expose the secret key in logs or responses.

### SQLite and cloud security

SQLite introduces specific deployment considerations:

* Store the database outside the public static directory.

* Use a persistent volume that survives redeployment and restarts.

* Do not keep the production database on an ephemeral filesystem.

* Restrict filesystem permissions for the database and its journal/WAL files.

* Use SQLite foreign-key enforcement and transactions.

* Keep write transactions short to reduce database locking.

* Use a single application instance for writes unless the deployment architecture has been explicitly tested for safe coordination.

* Back up the database consistently; use SQLite's backup API or another appropriate consistent backup mechanism.

* Test restoring both the database and required uploaded images.

* Do not place a SQLite database on an arbitrary network filesystem and assume it is safe for concurrent writers.

Migration trigger: Move to PostgreSQL when you need multiple app instances, higher write concurrency, managed database availability, or more demanding recovery and scaling requirements.

### Customer privacy and legal pages

* Collect only necessary customer information.

* Restrict access to names, phone numbers, and delivery addresses.

* Define data retention, deletion, and backup policies.

* Explain cookies, collection purposes, third-party services, and customer rights accurately.

* Establish clear COD, shipping, cancellation, return, and refund policies.

* Review applicable Indian data-protection, consumer-protection, e-commerce, and tax obligations before launch.

Terms and privacy content must reflect the actual business practices. They should not be treated as generic legal templates that guarantee compliance.

### Security testing requirements

Before launch, verify that:

1. Customers cannot access admin URLs or change their roles.

2. Customers cannot access another user's orders or addresses by changing an ID.

3. Forms without valid CSRF tokens are rejected.

4. Malformed quantities and manipulated prices are rejected.

5. Repeated checkout submissions do not duplicate stock deductions.

6. Concurrent purchases cannot sell more units than are available.

7. Cancelling an order restores stock only once.

8. Uploaded files cannot execute as code.

9. Production error pages do not expose stack traces or secrets.

10. The database and images can be restored from backups.

## 5. Development-ready implementation plan

Follow this order so each phase builds on a tested foundation.

## 01

Foundation and configuration

Milestone 1

* Create the Flask application factory.

* Install Flask, SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, and pytest.

* Configure SQLite, environment variables, logging, and migrations.

* Create `ShopSettings`, base templates, and shared navigation.

* Add a CLI command to create the first admin.

  Done when the application starts, the database initializes, and migrations work.

## 02

Authentication and account security

Milestone 2

* Registration, login, logout, and password changes.

* Password hashing and login rate limits.

* Customer/admin roles and protected routes.

* Customer profile and address management.

  Done when authorization tests prove customers cannot access other users' data or admin functions.

## 03

Storefront and product catalog

Milestone 3

* Home page, product listings, details, categories, search, and pagination.

* Product and category management.

* Product image validation and safe storage.

* Shop branding and configurable settings.

  Done when admins can manage products and customers can browse active products on desktop and mobile.

## 04

Inventory and cart

Milestone 4

* Persistent customer carts.

* Quantity validation and stock checks.

* Inventory adjustments and movement history.

* Low-stock warnings.

  Done when unavailable items cannot be purchased and every manual stock adjustment is auditable.

## 05

COD checkout and order management

Milestone 5

* Delivery address and shipping fee calculation.

* Order creation and immutable item snapshots.

* Transaction-safe stock deduction and duplicate prevention.

* Admin fulfillment workflow and COD collection tracking.

  Done when successful, repeated, cancelled, and concurrent order scenarios pass tests.

## 06

Hardening and cloud deployment

Milestone 6

* Terms, privacy, and shipping/return policies.

* Automated regression and security tests.

* Production WSGI server, HTTPS, persistent storage, and secure headers.

* Database/image backups and recovery testing.

  Done when a production-like deployment survives a restart and passes the release checklist.

## 6. Initial dependencies

Start with these packages in `requirements.txt`, then pin the tested versions before deployment.

```
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-Login
Flask-WTF
email-validator
pytest
gunicorn
```

SQLite support is included with Python's standard library. Add a maintained rate-limiting extension and an image-processing library when implementing those features. Keep development-only dependencies separate from production dependencies.

## 7. First development sprint

Start with the smallest testable vertical slice instead of creating every page at once.

## Sprint checklist

0 of 8

Create project structure and virtual environment

Foundation

Install dependencies and configure environment variables

Foundation

Build the Flask application factory and extensions

Foundation

Create User and ShopSettings models

Database

Set up SQLite and the first database migration

Database

Implement the secure admin-creation CLI command

Security

Build registration, login, logout, and role checks

Authentication

Write authentication and authorization tests

Testing

Copy checklist

## 8. Final release criteria

Do not launch until all of the following are true:

* The customer shopping journey works from registration to order confirmation.

* Admin access and customer data isolation are verified.

* Product prices and shipping charges are calculated server-side in INR.

* Stock changes and order creation are transaction-safe.

* COD collection and order fulfillment have separate statuses.

* The SQLite database is stored persistently in the cloud.

* Automated tests cover authentication, inventory, checkout, and cancellations.

* HTTPS, secure cookies, CSRF protection, and rate limits are enabled.

* Terms, privacy, shipping, and cancellation policies are published.

* Backups have been restored successfully in a test environment.

Recommended first coding task: implement the Flask application factory, configuration, database models, and secure admin-creation command. Once that foundation is tested, add authentication before building the storefront and shopping workflows.
