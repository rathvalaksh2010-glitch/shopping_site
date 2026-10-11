import os
import re
import secrets
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import (
    Flask, abort, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "instance", "shop.db")
UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
ALLOWED_IMAGES = {"png", "jpg", "jpeg", "gif", "webp"}

ORDER_STATUSES = ["PLACED", "CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"]
COD_STATUSES = ["PENDING", "COLLECTED", "FAILED"]
STATUS_TRANSITIONS = {
    "PLACED": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PACKED", "CANCELLED"],
    "PACKED": ["SHIPPED", "CANCELLED"],
    "SHIPPED": ["DELIVERED"],
    "DELIVERED": [],
    "CANCELLED": [],
}


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'customer',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS addresses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  recipient_name TEXT NOT NULL,
  phone TEXT NOT NULL,
  address_line_1 TEXT NOT NULL,
  address_line_2 TEXT,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  postal_code TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'India'
);
CREATE TABLE IF NOT EXISTS categories(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS products(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id INTEGER REFERENCES categories(id),
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  price INTEGER NOT NULL,
  image_path TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory(
  product_id INTEGER PRIMARY KEY REFERENCES products(id),
  quantity_available INTEGER NOT NULL DEFAULT 0 CHECK(quantity_available >= 0),
  low_stock_threshold INTEGER NOT NULL DEFAULT 5,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory_movements(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity_change INTEGER NOT NULL,
  reason TEXT,
  reference_type TEXT,
  reference_id INTEGER,
  created_by INTEGER,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS carts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cart_items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cart_id INTEGER NOT NULL REFERENCES carts(id),
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity INTEGER NOT NULL CHECK(quantity > 0),
  UNIQUE(cart_id, product_id)
);
CREATE TABLE IF NOT EXISTS orders(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_number TEXT NOT NULL UNIQUE,
  user_id INTEGER NOT NULL REFERENCES users(id),
  status TEXT NOT NULL,
  cod_payment_status TEXT NOT NULL DEFAULT 'PENDING',
  subtotal INTEGER NOT NULL,
  tax_amount INTEGER NOT NULL DEFAULT 0,
  shipping_amount INTEGER NOT NULL DEFAULT 0,
  discount_amount INTEGER NOT NULL DEFAULT 0,
  total_amount INTEGER NOT NULL,
  shipping_address_snapshot TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS order_items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  product_id INTEGER REFERENCES products(id),
  product_name_snapshot TEXT NOT NULL,
  unit_price INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  line_total INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS order_status_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  status TEXT NOT NULL,
  created_by INTEGER,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shop_settings(
  id INTEGER PRIMARY KEY CHECK (id = 1),
  shop_name TEXT NOT NULL,
  since INTEGER,
  shop_description TEXT,
  logo_path TEXT,
  contact_email TEXT,
  contact_phone TEXT,
  address TEXT,
  currency TEXT NOT NULL DEFAULT 'INR',
  shipping_fee INTEGER NOT NULL DEFAULT 0,
  tax_percent TEXT NOT NULL DEFAULT '0'
);
"""


def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower())
    return text.strip("-") or "item"


def unique_slug(table, base, ignore_id=None):
    slug, n = base, 2
    while True:
        row = query(f"SELECT id FROM {table} WHERE slug=?", (slug,), one=True)
        if not row or (ignore_id and row["id"] == ignore_id):
            return slug
        slug = f"{base}-{n}"
        n += 1


def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    db.execute(
        """INSERT OR IGNORE INTO shop_settings
           (id, shop_name, since, shop_description, logo_path, contact_email,
            contact_phone, address, currency, shipping_fee, tax_percent)
           VALUES (1,?,?,?,?,?,?,?,?,?,?)""",
        ("LAKSH Store", 2020, "Your everyday online shop.",
         None, "support@lakshstore.test", "+91 90000 00000",
         "Mumbai, India", "INR", 4900, "5"),
    )
    if not db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        ts = now()
        db.execute(
            """INSERT INTO users(name,email,password_hash,role,is_active,created_at,updated_at)
               VALUES(?,?,?,?,1,?,?)""",
            ("Administrator", "admin@shop.test",
             generate_password_hash("admin123"), "admin", ts, ts),
        )
    if not db.execute("SELECT 1 FROM categories").fetchone():
        cats = [("Electronics", "electronics", "Gadgets and devices"),
                ("Apparel", "apparel", "Clothing and accessories"),
                ("Home", "home", "Home and kitchen")]
        for name, slug, desc in cats:
            db.execute("INSERT INTO categories(name,slug,description) VALUES(?,?,?)",
                       (name, slug, desc))
        ts = now()
        seed = [
            (1, "Wireless Headphones", "wireless-headphones", "Over-ear Bluetooth headphones.", 249900, 12),
            (1, "Smart Watch", "smart-watch", "Fitness tracking smart watch.", 399900, 3),
            (2, "Cotton T-Shirt", "cotton-t-shirt", "Soft everyday cotton tee.", 79900, 25),
            (2, "Denim Jacket", "denim-jacket", "Classic blue denim jacket.", 199900, 6),
            (3, "Steel Water Bottle", "steel-water-bottle", "1L insulated bottle.", 59900, 40),
            (3, "Table Lamp", "table-lamp", "Warm LED reading lamp.", 129900, 4),
        ]
        for cid, name, slug, desc, price, qty in seed:
            cur = db.execute(
                """INSERT INTO products(category_id,name,slug,description,price,is_active,created_at,updated_at)
                   VALUES(?,?,?,?,?,1,?,?)""",
                (cid, name, slug, desc, price, ts, ts))
            db.execute(
                "INSERT INTO inventory(product_id,quantity_available,low_stock_threshold,updated_at) VALUES(?,?,?,?)",
                (cur.lastrowid, qty, 5, ts))
    db.commit()
    db.close()


# --------------------------------------------------------------------------
# Money helpers
# --------------------------------------------------------------------------
def rupees_to_paise(value):
    try:
        return int((Decimal(str(value).strip()) * 100).to_integral_value())
    except (InvalidOperation, ValueError, AttributeError):
        return None


def inr(paise):
    return "\u20b9{:,.2f}".format(Decimal(paise or 0) / 100)


app.jinja_env.filters["inr"] = inr
app.jinja_env.globals["inr"] = inr


# --------------------------------------------------------------------------
# CSRF + context
# --------------------------------------------------------------------------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        token = session.get("_csrf")
        if not token or token != request.form.get("csrf_token"):
            abort(400, "Invalid or missing CSRF token.")


@app.context_processor
def inject_globals():
    return {
        "shop": query("SELECT * FROM shop_settings WHERE id=1", one=True),
        "current_user": current_user(),
        "categories_nav": query("SELECT * FROM categories WHERE is_active=1 ORDER BY name"),
        "cart_count": cart_total_quantity(),
    }


# --------------------------------------------------------------------------
# Auth helpers
# --------------------------------------------------------------------------
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    return query("SELECT * FROM users WHERE id=? AND is_active=1", (uid,), one=True)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user()["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def get_or_create_cart(user_id):
    cart = query("SELECT * FROM carts WHERE user_id=?", (user_id,), one=True)
    if not cart:
        cur = execute("INSERT INTO carts(user_id,created_at,updated_at) VALUES(?,?,?)",
                      (user_id, now(), now()))
        cart = query("SELECT * FROM carts WHERE id=?", (cur.lastrowid,), one=True)
    return cart


def cart_total_quantity():
    if not session.get("uid"):
        return 0
    row = query(
        """SELECT COALESCE(SUM(ci.quantity),0) AS q FROM cart_items ci
           JOIN carts c ON c.id=ci.cart_id WHERE c.user_id=?""",
        (session["uid"],), one=True)
    return row["q"] if row else 0


def cart_lines(user_id):
    return query(
        """SELECT ci.id AS item_id, ci.quantity, p.*,
                  COALESCE(i.quantity_available,0) AS available
           FROM cart_items ci
           JOIN carts c ON c.id=ci.cart_id
           JOIN products p ON p.id=ci.product_id
           LEFT JOIN inventory i ON i.product_id=p.id
           WHERE c.user_id=? ORDER BY ci.id""",
        (user_id,))


def save_upload(file):
    if not file or not file.filename:
        return None
    if "." not in file.filename:
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_IMAGES:
        flash("Unsupported image type.", "error")
        return None
    name = f"{secrets.token_hex(8)}.{ext}"
    file.save(os.path.join(UPLOAD_DIR, name))
    return f"uploads/{name}"


# --------------------------------------------------------------------------
# Public: main
# --------------------------------------------------------------------------
@app.route("/")
def home():
    featured = query(
        """SELECT p.*, COALESCE(i.quantity_available,0) AS available
           FROM products p LEFT JOIN inventory i ON i.product_id=p.id
           WHERE p.is_active=1 ORDER BY p.created_at DESC LIMIT 8""")
    recent = query(
        """SELECT p.*, COALESCE(i.quantity_available,0) AS available
           FROM products p LEFT JOIN inventory i ON i.product_id=p.id
           WHERE p.is_active=1 ORDER BY p.id DESC LIMIT 4""")
    return render_template("home.html", featured=featured, recent=recent)


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# --------------------------------------------------------------------------
# Public: products
# --------------------------------------------------------------------------
def build_product_query(args):
    where = ["p.is_active=1"]
    params = []
    q = (args.get("q") or "").strip()
    if q:
        where.append("p.name LIKE ?")
        params.append(f"%{q}%")
    cat = args.get("category")
    if cat:
        where.append("c.slug=?")
        params.append(cat)
    sorts = {
        "newest": "p.created_at DESC",
        "price_asc": "p.price ASC",
        "price_desc": "p.price DESC",
        "name": "p.name ASC",
    }
    order = sorts.get(args.get("sort"), sorts["newest"])
    sql = f"""SELECT p.*, COALESCE(i.quantity_available,0) AS available, c.name AS category_name, c.slug AS category_slug
              FROM products p
              LEFT JOIN inventory i ON i.product_id=p.id
              LEFT JOIN categories c ON c.id=p.category_id
              WHERE {' AND '.join(where)} ORDER BY {order}"""
    return sql, params


@app.route("/products")
def products():
    sql, params = build_product_query(request.args)
    page = max(1, request.args.get("page", type=int) or 1)
    per_page = 8
    all_rows = query(sql, params)
    total = len(all_rows)
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)
    items = all_rows[(page - 1) * per_page: page * per_page]
    return render_template("products.html", products=items, page=page, pages=pages,
                           total=total, args=request.args)


@app.route("/products/<slug>")
def product_detail(slug):
    product = query(
        """SELECT p.*, COALESCE(i.quantity_available,0) AS available,
                  COALESCE(i.low_stock_threshold,5) AS low_stock_threshold,
                  c.name AS category_name, c.slug AS category_slug
           FROM products p LEFT JOIN inventory i ON i.product_id=p.id
           LEFT JOIN categories c ON c.id=p.category_id
           WHERE p.slug=? AND p.is_active=1""", (slug,), one=True)
    if not product:
        abort(404)
    return render_template("product_detail.html", product=product)


@app.route("/categories/<slug>")
def category(slug):
    cat = query("SELECT * FROM categories WHERE slug=? AND is_active=1", (slug,), one=True)
    if not cat:
        abort(404)
    sql, params = build_product_query({**request.args, "category": slug})
    cat_products = query(sql, params)
    return render_template("category.html", category=cat, products=cat_products)


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        pw = request.form.get("password") or ""
        pw2 = request.form.get("confirm") or ""
        if not name or not email or not pw:
            flash("All fields are required.", "error")
        elif "@" not in email:
            flash("Enter a valid email address.", "error")
        elif len(pw) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif pw != pw2:
            flash("Passwords do not match.", "error")
        elif query("SELECT 1 FROM users WHERE email=?", (email,), one=True):
            flash("An account with that email already exists.", "error")
        elif request.form.get("accept_terms") != "on":
            flash("You must accept the terms and conditions.", "error")
        else:
            ts = now()
            cur = execute(
                """INSERT INTO users(name,email,password_hash,role,is_active,created_at,updated_at)
                   VALUES(?,?,?,'customer',1,?,?)""",
                (name, email, generate_password_hash(pw), ts, ts))
            session.clear()
            session["uid"] = cur.lastrowid
            flash("Welcome, your account is ready.", "success")
            return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or request.form.get("username") or "").strip().lower()
        pw = request.form.get("password") or request.form.get("passwd") or ""
        user = query("SELECT * FROM users WHERE email=? AND is_active=1", (email,), one=True)
        if user and check_password_hash(user["password_hash"], pw):
            session.clear()
            session["uid"] = user["id"]
            flash(f"Welcome back, {user['name']}.", "success")
            nxt = request.args.get("next")
            if nxt and nxt.startswith("/"):
                return redirect(nxt)
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "home"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# --------------------------------------------------------------------------
# Account
# --------------------------------------------------------------------------
@app.route("/account")
@login_required
def account():
    user = current_user()
    addresses = query("SELECT * FROM addresses WHERE user_id=? ORDER BY id DESC", (user["id"],))
    return render_template("account.html", addresses=addresses)


@app.route("/account/addresses", methods=["POST"])
@login_required
def account_addresses():
    f = request.form
    required = ["recipient_name", "phone", "address_line_1", "city", "state", "postal_code"]
    if any(not (f.get(k) or "").strip() for k in required):
        flash("Please complete all required address fields.", "error")
    else:
        execute(
            """INSERT INTO addresses(user_id,recipient_name,phone,address_line_1,address_line_2,
               city,state,postal_code,country) VALUES(?,?,?,?,?,?,?,?,?)""",
            (current_user()["id"], f["recipient_name"], f["phone"], f["address_line_1"],
             f.get("address_line_2"), f["city"], f["state"], f["postal_code"],
             f.get("country") or "India"))
        flash("Address saved.", "success")
    return redirect(url_for("account"))


@app.route("/account/password", methods=["POST"])
@login_required
def account_password():
    user = current_user()
    old = request.form.get("old_password") or ""
    new = request.form.get("new_password") or ""
    if not check_password_hash(user["password_hash"], old):
        flash("Current password is incorrect.", "error")
    elif len(new) < 8:
        flash("New password must be at least 8 characters.", "error")
    else:
        execute("UPDATE users SET password_hash=?, updated_at=? WHERE id=?",
                (generate_password_hash(new), now(), user["id"]))
        flash("Password updated.", "success")
    return redirect(url_for("account"))


@app.route("/account/orders")
@login_required
def account_orders():
    orders = query("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",
                   (current_user()["id"],))
    return render_template("account_orders.html", orders=orders)


@app.route("/account/orders/<order_number>")
@login_required
def account_order(order_number):
    order = query("SELECT * FROM orders WHERE order_number=? AND user_id=?",
                  (order_number, current_user()["id"]), one=True)
    if not order:
        abort(404)
    return render_order(order)


def render_order(order):
    items = query("SELECT * FROM order_items WHERE order_id=?", (order["id"],))
    history = query("SELECT * FROM order_status_history WHERE order_id=? ORDER BY id",
                    (order["id"],))
    return render_template("order_confirmation.html", order=order, items=items, history=history)


# --------------------------------------------------------------------------
# Cart
# --------------------------------------------------------------------------
@app.route("/cart")
@login_required
def cart():
    items = cart_lines(current_user()["id"])
    settings = query("SELECT * FROM shop_settings WHERE id=1", one=True)
    subtotal = sum(i["price"] * i["quantity"] for i in items)
    shipping = settings["shipping_fee"]
    tax = int(subtotal * Decimal(settings["tax_percent"]) / 100)
    return render_template("cart.html", items=items, subtotal=subtotal,
                           shipping=shipping, tax=tax, total=subtotal + shipping + tax)


@app.route("/cart/items", methods=["POST"])
@login_required
def cart_add():
    product_id = request.form.get("product_id", type=int)
    qty = request.form.get("quantity", type=int) or 1
    product = query("SELECT * FROM products WHERE id=? AND is_active=1", (product_id,), one=True)
    if not product:
        flash("Product not available.", "error")
        return redirect(url_for("products"))
    inv = query("SELECT * FROM inventory WHERE product_id=?", (product_id,), one=True)
    available = inv["quantity_available"] if inv else 0
    if qty < 1:
        qty = 1
    cart = get_or_create_cart(current_user()["id"])
    existing = query("SELECT * FROM cart_items WHERE cart_id=? AND product_id=?",
                     (cart["id"], product_id), one=True)
    new_qty = qty + (existing["quantity"] if existing else 0)
    if new_qty > available:
        flash(f"Only {available} in stock.", "error")
    elif existing:
        execute("UPDATE cart_items SET quantity=? WHERE id=?", (new_qty, existing["id"]))
        flash("Cart updated.", "success")
    else:
        execute("INSERT INTO cart_items(cart_id,product_id,quantity) VALUES(?,?,?)",
                (cart["id"], product_id, qty))
        flash("Added to cart.", "success")
    return redirect(request.form.get("next") or url_for("products"))


@app.route("/cart/items/<int:item_id>/update", methods=["POST"])
@login_required
def cart_update(item_id):
    qty = request.form.get("quantity", type=int) or 1
    item = query(
        """SELECT ci.*, COALESCE(i.quantity_available,0) AS available
           FROM cart_items ci JOIN carts c ON c.id=ci.cart_id
           LEFT JOIN inventory i ON i.product_id=ci.product_id
           WHERE ci.id=? AND c.user_id=?""",
        (item_id, current_user()["id"]), one=True)
    if not item:
        abort(404)
    if qty < 1:
        execute("DELETE FROM cart_items WHERE id=?", (item_id,))
    elif qty > item["available"]:
        flash(f"Only {item['available']} in stock.", "error")
    else:
        execute("UPDATE cart_items SET quantity=? WHERE id=?", (qty, item_id))
    return redirect(url_for("cart"))


@app.route("/cart/items/<int:item_id>/remove", methods=["POST"])
@login_required
def cart_remove(item_id):
    item = query(
        """SELECT ci.id FROM cart_items ci JOIN carts c ON c.id=ci.cart_id
           WHERE ci.id=? AND c.user_id=?""",
        (item_id, current_user()["id"]), one=True)
    if not item:
        abort(404)
    execute("DELETE FROM cart_items WHERE id=?", (item_id,))
    flash("Item removed.", "success")
    return redirect(url_for("cart"))


# --------------------------------------------------------------------------
# Checkout (COD)
# --------------------------------------------------------------------------
def order_number():
    return "ORD" + datetime.utcnow().strftime("%Y%m%d") + secrets.token_hex(3).upper()


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    user = current_user()
    items = cart_lines(user["id"])
    settings = query("SELECT * FROM shop_settings WHERE id=1", one=True)
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))

    subtotal = sum(i["price"] * i["quantity"] for i in items)
    shipping = settings["shipping_fee"]
    tax = int(subtotal * Decimal(settings["tax_percent"]) / 100)
    total = subtotal + shipping + tax

    if request.method == "POST":
        token = request.form.get("checkout_token")
        if not token or token != session.get("checkout_token"):
            flash("This order was already placed.", "error")
            return redirect(url_for("account_orders"))

        address_id = request.form.get("address_id", type=int)
        if address_id:
            addr = query("SELECT * FROM addresses WHERE id=? AND user_id=?",
                         (address_id, user["id"]), one=True)
        else:
            f = request.form
            if any(not (f.get(k) or "").strip() for k in
                   ["recipient_name", "phone", "address_line_1", "city", "state", "postal_code"]):
                flash("Please provide a complete delivery address.", "error")
                return redirect(url_for("checkout"))
            addr = {"recipient_name": f["recipient_name"], "phone": f["phone"],
                    "address_line_1": f["address_line_1"], "address_line_2": f.get("address_line_2"),
                    "city": f["city"], "state": f["state"], "postal_code": f["postal_code"],
                    "country": f.get("country") or "India"}

        db = get_db()
        try:
            db.execute("BEGIN")
            # Re-validate stock and recompute totals from current DB values.
            server_subtotal = 0
            for it in items:
                fresh = query(
                    """SELECT p.price, p.name, COALESCE(i.quantity_available,0) AS available
                       FROM products p LEFT JOIN inventory i ON i.product_id=p.id
                       WHERE p.id=? AND p.is_active=1""", (it["id"],), one=True)
                if not fresh or fresh["available"] < it["quantity"]:
                    raise ValueError(f"'{it['name']}' is no longer available in the requested quantity.")
                server_subtotal += fresh["price"] * it["quantity"]

            server_tax = int(server_subtotal * Decimal(settings["tax_percent"]) / 100)
            server_total = server_subtotal + shipping + server_tax

            cur = db.execute(
                """INSERT INTO orders(order_number,user_id,status,cod_payment_status,subtotal,
                   tax_amount,shipping_amount,discount_amount,total_amount,
                   shipping_address_snapshot,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (order_number(), user["id"], "PLACED", "PENDING", server_subtotal,
                 server_tax, shipping, 0, server_total,
                 f"{addr['recipient_name']}, {addr['phone']}, {addr['address_line_1']}, "
                 f"{addr.get('address_line_2') or ''}, {addr['city']}, {addr['state']} "
                 f"{addr['postal_code']}, {addr['country']}".replace(", ,", ","),
                 now(), now()))
            order_id = cur.lastrowid

            for it in items:
                # Conditional, concurrency-safe deduction.
                upd = db.execute(
                    """UPDATE inventory SET quantity_available = quantity_available - ?, updated_at=?
                       WHERE product_id=? AND quantity_available >= ?""",
                    (it["quantity"], now(), it["id"], it["quantity"]))
                if upd.rowcount != 1:
                    raise ValueError(f"Insufficient stock for '{it['name']}'.")
                line_total = it["price"] * it["quantity"]
                db.execute(
                    """INSERT INTO order_items(order_id,product_id,product_name_snapshot,
                       unit_price,quantity,line_total) VALUES(?,?,?,?,?,?)""",
                    (order_id, it["id"], it["name"], it["price"], it["quantity"], line_total))
                db.execute(
                    """INSERT INTO inventory_movements(product_id,quantity_change,reason,
                       reference_type,reference_id,created_by,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (it["id"], -it["quantity"], "Order placed", "order", order_id, user["id"], now()))
            db.execute("INSERT INTO order_status_history(order_id,status,created_by,created_at) VALUES(?,?,?,?)",
                       (order_id, "PLACED", user["id"], now()))
            db.execute("DELETE FROM cart_items WHERE cart_id=(SELECT id FROM carts WHERE user_id=?)",
                       (user["id"],))
            db.commit()
        except ValueError as e:
            db.rollback()
            flash(str(e), "error")
            return redirect(url_for("cart"))
        except Exception:
            db.rollback()
            app.logger.exception("checkout failed")
            flash("Could not place order. Please try again.", "error")
            return redirect(url_for("cart"))

        session.pop("checkout_token", None)
        flash("Order placed successfully.", "success")
        order = query("SELECT * FROM orders WHERE id=?", (order_id,), one=True)
        return redirect(url_for("account_order", order_number=order["order_number"]))

    token = secrets.token_hex(16)
    session["checkout_token"] = token
    addresses = query("SELECT * FROM addresses WHERE user_id=? ORDER BY id DESC", (user["id"],))
    return render_template("checkout.html", items=items, subtotal=subtotal, shipping=shipping,
                           tax=tax, total=total, addresses=addresses, checkout_token=token)


@app.route("/orders/<order_number>")
@login_required
def order_detail(order_number):
    return redirect(url_for("account_order", order_number=order_number))


# --------------------------------------------------------------------------
# Admin
# --------------------------------------------------------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "orders": query("SELECT COUNT(*) c FROM orders", one=True)["c"],
        "customers": query("SELECT COUNT(*) c FROM users WHERE role='customer'", one=True)["c"],
        "products": query("SELECT COUNT(*) c FROM products", one=True)["c"],
        "revenue": query("SELECT COALESCE(SUM(total_amount),0) s FROM orders WHERE status!='CANCELLED'", one=True)["s"],
    }
    low_stock = query(
        """SELECT p.id,p.name,i.quantity_available,i.low_stock_threshold
           FROM inventory i JOIN products p ON p.id=i.product_id
           WHERE i.quantity_available <= i.low_stock_threshold ORDER BY i.quantity_available""")
    recent = query("SELECT * FROM orders ORDER BY id DESC LIMIT 8")
    return render_template("admin/dashboard.html", stats=stats, low_stock=low_stock, recent=recent)


@app.route("/admin/products")
@admin_required
def admin_products():
    rows = query(
        """SELECT p.*, COALESCE(i.quantity_available,0) AS available, c.name AS category_name
           FROM products p LEFT JOIN inventory i ON i.product_id=p.id
           LEFT JOIN categories c ON c.id=p.category_id ORDER BY p.id DESC""")
    return render_template("admin/products.html", products=rows)


@app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    return product_form(None)


@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(pid):
    product = query("SELECT * FROM products WHERE id=?", (pid,), one=True)
    if not product:
        abort(404)
    return product_form(product)


def product_form(product):
    cats = query("SELECT * FROM categories ORDER BY name")
    if request.method == "POST":
        f = request.form
        name = (f.get("name") or "").strip()
        price = rupees_to_paise(f.get("price"))
        category_id = f.get("category_id", type=int)
        if not name or price is None or price < 0:
            flash("Provide a valid name and non-negative price.", "error")
        else:
            image = save_upload(request.files.get("image"))
            if image is None and product is not None:
                image = product["image_path"]
            if image is None and f.get("image_path"):
                image = f.get("image_path")
            ts = now()
            if product is None:
                slug = unique_slug("products", slugify(name))
                cur = execute(
                    """INSERT INTO products(category_id,name,slug,description,price,image_path,is_active,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (category_id, name, slug, f.get("description"), price, image,
                     1 if f.get("is_active") else 0, ts, ts))
                qty = f.get("quantity", type=int) or 0
                execute("INSERT INTO inventory(product_id,quantity_available,low_stock_threshold,updated_at) VALUES(?,?,?,?)",
                        (cur.lastrowid, qty, f.get("low_stock_threshold", type=int) or 5, ts))
                if qty:
                    execute("""INSERT INTO inventory_movements(product_id,quantity_change,reason,reference_type,created_by,created_at)
                               VALUES(?,?,?,?,?,?)""",
                            (cur.lastrowid, qty, "Initial stock", "manual", current_user()["id"], ts))
                flash("Product created.", "success")
            else:
                slug = unique_slug("products", slugify(name), ignore_id=product["id"])
                execute(
                    """UPDATE products SET category_id=?,name=?,slug=?,description=?,price=?,
                       image_path=?,is_active=?,updated_at=? WHERE id=?""",
                    (category_id, name, slug, f.get("description"), price, image,
                     1 if f.get("is_active") else 0, ts, product["id"]))
                flash("Product updated.", "success")
            return redirect(url_for("admin_products"))
    return render_template("admin/product_form.html", product=product, categories=cats)


@app.route("/admin/products/<int:pid>/archive", methods=["POST"])
@admin_required
def admin_product_archive(pid):
    execute("UPDATE products SET is_active=0, updated_at=? WHERE id=?", (now(), pid))
    flash("Product archived.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Category name is required.", "error")
        else:
            slug = unique_slug("categories", slugify(name))
            execute("INSERT INTO categories(name,slug,description,is_active) VALUES(?,?,?,1)",
                    (name, slug, request.form.get("description")))
            flash("Category created.", "success")
        return redirect(url_for("admin_categories"))
    cats = query("""SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id=c.id) AS product_count
                    FROM categories c ORDER BY c.name""")
    return render_template("admin/categories.html", categories=cats)


@app.route("/admin/categories/<int:cid>/edit", methods=["POST"])
@admin_required
def admin_category_edit(cid):
    cat = query("SELECT * FROM categories WHERE id=?", (cid,), one=True)
    if not cat:
        abort(404)
    name = (request.form.get("name") or "").strip()
    if name:
        execute("UPDATE categories SET name=?,description=?,is_active=? WHERE id=?",
                (name, request.form.get("description"),
                 1 if request.form.get("is_active") else 0, cid))
        flash("Category updated.", "success")
    return redirect(url_for("admin_categories"))


@app.route("/admin/inventory")
@admin_required
def admin_inventory():
    inv = query(
        """SELECT p.id,p.name,i.quantity_available,i.low_stock_threshold,i.updated_at
           FROM products p JOIN inventory i ON i.product_id=p.id ORDER BY p.name""")
    movements = query(
        """SELECT m.*, p.name AS product_name FROM inventory_movements m
           JOIN products p ON p.id=m.product_id ORDER BY m.id DESC LIMIT 50""")
    return render_template("admin/inventory.html", inventory=inv, movements=movements)


@app.route("/admin/inventory/adjustments", methods=["POST"])
@admin_required
def admin_inventory_adjust():
    pid = request.form.get("product_id", type=int)
    change = request.form.get("quantity_change", type=int)
    reason = (request.form.get("reason") or "").strip() or "Manual adjustment"
    inv = query("SELECT * FROM inventory WHERE product_id=?", (pid,), one=True)
    if not inv or change is None or change == 0:
        flash("Invalid adjustment.", "error")
    elif inv["quantity_available"] + change < 0:
        flash("Adjustment would result in negative stock.", "error")
    else:
        execute("UPDATE inventory SET quantity_available=quantity_available+?, updated_at=? WHERE product_id=?",
                (change, now(), pid))
        execute("""INSERT INTO inventory_movements(product_id,quantity_change,reason,reference_type,created_by,created_at)
                   VALUES(?,?,?,?,?,?)""",
                (pid, change, reason, "manual", current_user()["id"], now()))
        flash("Stock adjusted.", "success")
    return redirect(url_for("admin_inventory"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    status = request.args.get("status")
    if status in ORDER_STATUSES:
        orders = query("SELECT o.*, u.name AS customer FROM orders o JOIN users u ON u.id=o.user_id WHERE o.status=? ORDER BY o.id DESC", (status,))
    else:
        orders = query("SELECT o.*, u.name AS customer FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC")
    return render_template("admin/orders.html", orders=orders, statuses=ORDER_STATUSES, current_status=status)


@app.route("/admin/orders/<int:oid>")
@admin_required
def admin_order(oid):
    order = query("SELECT o.*, u.name AS customer, u.email FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", (oid,), one=True)
    if not order:
        abort(404)
    items = query("SELECT * FROM order_items WHERE order_id=?", (oid,))
    history = query("SELECT * FROM order_status_history WHERE order_id=? ORDER BY id", (oid,))
    allowed = STATUS_TRANSITIONS.get(order["status"], [])
    return render_template("admin/order_detail.html", order=order, items=items,
                           history=history, allowed=allowed, cod_statuses=COD_STATUSES)


@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
@admin_required
def admin_order_status(oid):
    order = query("SELECT * FROM orders WHERE id=?", (oid,), one=True)
    if not order:
        abort(404)
    new_status = request.form.get("status")
    cod = request.form.get("cod_payment_status")
    if new_status and new_status not in STATUS_TRANSITIONS.get(order["status"], []):
        flash("Invalid status transition.", "error")
    elif new_status:
        db = get_db()
        db.execute("UPDATE orders SET status=?, updated_at=? WHERE id=?", (new_status, now(), oid))
        db.execute("INSERT INTO order_status_history(order_id,status,created_by,created_at) VALUES(?,?,?,?)",
                   (oid, new_status, current_user()["id"], now()))
        if new_status == "CANCELLED" and order["status"] != "CANCELLED":
            for it in query("SELECT * FROM order_items WHERE order_id=?", (oid,)):
                db.execute("UPDATE inventory SET quantity_available=quantity_available+?, updated_at=? WHERE product_id=?",
                           (it["quantity"], now(), it["product_id"]))
                db.execute("""INSERT INTO inventory_movements(product_id,quantity_change,reason,reference_type,reference_id,created_by,created_at)
                              VALUES(?,?,?,?,?,?,?)""",
                           (it["product_id"], it["quantity"], "Order cancelled", "order", oid, current_user()["id"], now()))
        db.commit()
        flash("Order status updated.", "success")
    if cod in COD_STATUSES:
        execute("UPDATE orders SET cod_payment_status=?, updated_at=? WHERE id=?", (cod, now(), oid))
        flash("Payment status updated.", "success")
    return redirect(url_for("admin_order", oid=oid))


@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    if request.method == "POST":
        f = request.form
        fee = rupees_to_paise(f.get("shipping_fee")) or 0
        logo = save_upload(request.files.get("logo"))
        if logo is None:
            logo = f.get("logo_path") or query("SELECT logo_path FROM shop_settings WHERE id=1", one=True)["logo_path"]
        execute(
            """UPDATE shop_settings SET shop_name=?, since=?, shop_description=?, logo_path=?,
               contact_email=?, contact_phone=?, address=?, currency=?, shipping_fee=?,
               tax_percent=? WHERE id=1""",
            (f.get("shop_name") or "Shop", f.get("since", type=int), f.get("shop_description"),
             logo, f.get("contact_email"), f.get("contact_phone"), f.get("address"),
             f.get("currency") or "INR", fee, f.get("tax_percent") or "0"))
        flash("Settings saved.", "success")
        return redirect(url_for("admin_settings"))
    return render_template("admin/settings.html")


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="You do not have access to this page."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, message="Bad request."), 400


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
