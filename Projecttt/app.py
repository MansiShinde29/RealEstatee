from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session tracking

# Initialize database
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)
    cur.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", "admin123", "admin"))

    # Other tables
    cur.execute("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, property TEXT, tenant TEXT, amount REAL, payment_type TEXT, txn_id TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS tenants (id INTEGER PRIMARY KEY, name TEXT, issue TEXT, status TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, name TEXT, location TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, role TEXT)")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# Admin-only route decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session or session.get("role") != "admin":
            flash("Access denied! Admins only.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/dashboard")
@admin_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/rent", methods=["GET", "POST"])
@admin_required
def rent():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    if request.method == "POST":
        property_name = request.form["property"]
        tenant = request.form["tenant"]
        amount = request.form["amount"]
        payment_type = request.form["payment_type"]
        txn_id = request.form["txn_id"]
        cur.execute("INSERT INTO payments (property, tenant, amount, payment_type, txn_id) VALUES (?, ?, ?, ?, ?)",
                    (property_name, tenant, amount, payment_type, txn_id))
        conn.commit()
    cur.execute("SELECT * FROM payments")
    payments = cur.fetchall()
    conn.close()
    return render_template("rent.html", payments=payments)

@app.route("/tenants", methods=["GET", "POST"])
@admin_required
def tenants():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    if request.method == "POST":
        tenant_name = request.form["tenant_name"]
        issue = request.form["issue"]
        status = request.form["status"]
        cur.execute("INSERT INTO tenants (name, issue, status) VALUES (?, ?, ?)",
                    (tenant_name, issue, status))
        conn.commit()
    cur.execute("SELECT * FROM tenants")
    tenants = cur.fetchall()
    conn.close()
    return render_template("tenants.html", tenants=tenants)

@app.route("/employees", methods=["GET", "POST"])
@admin_required
def employees():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        role = request.form["role"]
        cur.execute("INSERT INTO employees (name, role) VALUES (?, ?)", (name, role))
        conn.commit()
    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()
    conn.close()
    return render_template("employees.html", employees=employees)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session["username"] = user[1]
            session["role"] = user[3]
            flash("Login successful!", "success")
            return redirect("/dashboard")
        else:
            flash("Invalid credentials!", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)", 
                    (name, email, message))
        conn.commit()
        conn.close()
        return redirect(url_for("thank_you"))
    return render_template("contact.html")

@app.route("/thank-you")
def thank_you():
    return "<h1>Thank you for contacting us! We'll get back to you soon.</h1>"

@app.route("/admin/contact")
@admin_required
def view_contacts():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM contact_messages")
    messages = cur.fetchall()
    conn.close()
    return render_template("admin_contacts.html", messages=messages)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

if __name__ == "__main__":
    app.run(debug=True)