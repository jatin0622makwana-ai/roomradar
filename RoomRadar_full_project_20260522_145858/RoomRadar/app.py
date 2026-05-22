from functools import wraps
import hashlib
import os
import sqlite3

from flask import Flask, jsonify, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = "roomradar_secret_key_2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", BASE_DIR), "RoomRadar")
DB_PATH = os.environ.get("ROOMRADAR_DB_PATH", os.path.join(DEFAULT_DATA_DIR, "roomradar.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

BUDGET_RANGES = {
    "below_5000": ("price < ?", [5000]),
    "5000_10000": ("price BETWEEN ? AND ?", [5000, 10000]),
    "above_10000": ("price > ?", [10000]),
}

BUDGET_ALIASES = {
    "Below ₹5000": "below_5000",
    "Below Rs.5000": "below_5000",
    "Below Rs. 5000": "below_5000",
    "₹5000 - ₹10000": "5000_10000",
    "Rs.5000 - Rs.10000": "5000_10000",
    "Rs. 5000 - Rs. 10000": "5000_10000",
    "Above ₹10000": "above_10000",
    "Above Rs.10000": "above_10000",
    "Above Rs. 10000": "above_10000",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            city TEXT NOT NULL,
            area TEXT NOT NULL,
            stay_type TEXT NOT NULL,
            gender TEXT NOT NULL,
            price INTEGER NOT NULL,
            facilities TEXT NOT NULL,
            image_url TEXT,
            owner_id INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            listing_id INTEGER REFERENCES listings(id),
            user_id INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    demo = [
        ("Budget PG", "Paldi, Ahmedabad", "Ahmedabad", "Paldi", "PG", "Male", 4200, "WiFi,Food,Laundry", "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?q=80&w=800&auto=format&fit=crop"),
        ("Comfort PG", "Navrangpura, Ahmedabad", "Ahmedabad", "Navrangpura", "PG", "Male", 6500, "WiFi,Food,AC", "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?q=80&w=800&auto=format&fit=crop"),
        ("Urban Flat", "Satellite, Ahmedabad", "Ahmedabad", "Satellite", "Flat", "Any", 12000, "Parking,Kitchen,WiFi", "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=800&auto=format&fit=crop"),
        ("Student Hostel", "Vastrapur, Ahmedabad", "Ahmedabad", "Vastrapur", "Hostel", "Male", 4500, "Food,WiFi,Laundry", "https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=800&auto=format&fit=crop"),
        ("Green PG", "Bopal, Ahmedabad", "Ahmedabad", "Bopal", "PG", "Female", 5500, "WiFi,AC,Food", "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?q=80&w=800&auto=format&fit=crop"),
        ("City Hostel", "Maninagar, Ahmedabad", "Ahmedabad", "Maninagar", "Hostel", "Any", 3800, "WiFi,Laundry", "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?q=80&w=800&auto=format&fit=crop"),
        ("Premium Flat", "Prahlad Nagar, Ahmedabad", "Ahmedabad", "Prahlad Nagar", "Flat", "Any", 18000, "Parking,Kitchen,WiFi,AC", "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?q=80&w=800&auto=format&fit=crop"),
    ]
    for listing in demo:
        exists = cur.execute(
            "SELECT id FROM listings WHERE title=? AND location=?",
            (listing[0], listing[1]),
        ).fetchone()
        if not exists:
            cur.execute(
                """
                INSERT INTO listings (title, location, city, area, stay_type, gender, price, facilities, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                listing,
            )

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return decorated


def row_to_listing(row):
    item = dict(row)
    item["facilities"] = [facility.strip() for facility in item["facilities"].split(",") if facility.strip()]
    return item


def is_safe_next(target):
    return target and target.startswith("/") and not target.startswith("//")


def normalize_budget(value):
    return BUDGET_ALIASES.get(value, value)


@app.route("/")
def home():
    return render_template("homepage.html", user=session.get("user_name"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.form.get("next") or request.args.get("next")

        if not email or not password:
            return render_template("login.html", error="Please fill in all fields.")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, hash_password(password)),
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            if is_safe_next(next_url):
                return redirect(next_url)
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([email, new_password, confirm]):
            return render_template("reset_password.html", error="Please fill in all fields.")
        if new_password != confirm:
            return render_template("reset_password.html", error="Passwords do not match.")
        if len(new_password) < 6:
            return render_template("reset_password.html", error="Password must be at least 6 characters.")

        conn = get_db()
        cur = conn.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hash_password(new_password), email),
        )
        conn.commit()
        conn.close()

        if cur.rowcount == 0:
            return render_template("reset_password.html", error="No account found for this email.")

        return redirect(url_for("login", success="Password updated. Please log in."))

    return render_template("reset_password.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([name, email, phone, password, confirm]):
            return render_template("signup.html", error="Please fill in all fields.")

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match.")

        if len(password) < 6:
            return render_template("signup.html", error="Password must be at least 6 characters.")

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
                (name, email, phone, hash_password(password)),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login", success="Account created! Please log in."))
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Email already registered.")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/listings")
def listings():
    city = request.args.get("city", "").strip()
    area = request.args.get("area", "").strip()
    stay_type = request.args.get("stay_type", "").strip()
    budget = normalize_budget(request.args.get("budget", "").strip())
    gender = request.args.get("gender", "").strip()

    query = "SELECT * FROM listings WHERE 1=1"
    params = []

    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")
    if area:
        query += " AND (area LIKE ? OR location LIKE ?)"
        params.extend([f"%{area}%", f"%{area}%"])
    if stay_type:
        query += " AND stay_type=?"
        params.append(stay_type)
    if gender:
        query += " AND (gender=? OR gender='Any')"
        params.append(gender)
    if budget in BUDGET_RANGES:
        clause, values = BUDGET_RANGES[budget]
        query += f" AND {clause}"
        params.extend(values)

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        "listings.html",
        listings=[row_to_listing(row) for row in rows],
        filters={"city": city, "area": area, "stay_type": stay_type, "budget": budget, "gender": gender},
        user=session.get("user_name"),
    )


@app.route("/listings/<int:listing_id>")
def listing_detail(listing_id):
    conn = get_db()
    row = conn.execute(
        """
        SELECT listings.*, users.name AS owner_name, users.email AS owner_email, users.phone AS owner_phone
        FROM listings
        LEFT JOIN users ON users.id = listings.owner_id
        WHERE listings.id=?
        """,
        (listing_id,),
    ).fetchone()
    conn.close()

    listing = row_to_listing(row) if row else None
    status = 200 if listing else 404
    return render_template("detail.html", listing=listing, user=session.get("user_name")), status


@app.route("/roommates")
def roommates():
    roommate_profiles = [
        {
            "name": "Aarav Patel",
            "location": "Navrangpura, Ahmedabad",
            "budget": 7000,
            "gender": "Male",
            "occupation": "Student",
            "preferences": ["Non-smoker", "Early riser", "Vegetarian"],
        },
        {
            "name": "Meera Shah",
            "location": "Bopal, Ahmedabad",
            "budget": 6500,
            "gender": "Female",
            "occupation": "Working Professional",
            "preferences": ["Quiet space", "AC room", "Female roommate"],
        },
        {
            "name": "Rohan Mehta",
            "location": "Satellite, Ahmedabad",
            "budget": 10000,
            "gender": "Male",
            "occupation": "Intern",
            "preferences": ["Shared flat", "WiFi", "Parking"],
        },
        {
            "name": "Nisha Verma",
            "location": "Vastrapur, Ahmedabad",
            "budget": 8000,
            "gender": "Female",
            "occupation": "Student",
            "preferences": ["Near college", "Food included", "Laundry"],
        },
    ]
    return render_template("roommates.html", roommates=roommate_profiles, user=session.get("user_name"))


@app.route("/compare")
def compare():
    listing_ids = []
    for raw_id in request.args.getlist("id") + request.args.getlist("ids"):
        try:
            item_id = int(raw_id)
            if item_id not in listing_ids:
                listing_ids.append(item_id)
        except ValueError:
            continue

    conn = get_db()
    all_rows = conn.execute("SELECT * FROM listings ORDER BY price").fetchall()
    all_listings = [row_to_listing(row) for row in all_rows]
    listings_to_compare = []

    if listing_ids:
        placeholders = ",".join("?" for _ in listing_ids)
        rows = conn.execute(
            f"SELECT * FROM listings WHERE id IN ({placeholders}) ORDER BY price",
            listing_ids,
        ).fetchall()
        listings_to_compare = [row_to_listing(row) for row in rows]

    conn.close()

    return render_template(
        "compare.html",
        listings=listings_to_compare,
        all_listings=all_listings,
        selected_ids=listing_ids,
        user=session.get("user_name"),
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    listing_id = request.values.get("listing_id", type=int)
    listing = None
    if listing_id:
        conn = get_db()
        listing = conn.execute("SELECT id, title, location FROM listings WHERE id=?", (listing_id,)).fetchone()
        conn.close()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not all([name, email, message]):
            return render_template(
                "contact.html",
                error="Please fill in all fields.",
                user=session.get("user_name"),
                listing=listing,
            )

        conn = get_db()
        conn.execute(
            """
            INSERT INTO contact_messages (name, email, message, listing_id, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, message, listing_id, session.get("user_id")),
        )
        conn.commit()
        conn.close()
        return render_template("contact.html", success=True, user=session.get("user_name"), listing=listing)

    current_user = None
    if session.get("user_id"):
        conn = get_db()
        current_user = conn.execute("SELECT name, email FROM users WHERE id=?", (session["user_id"],)).fetchone()
        conn.close()

    return render_template(
        "contact.html",
        user=session.get("user_name"),
        current_user=current_user,
        listing=listing,
    )


@app.route("/list-property", methods=["GET", "POST"])
@login_required
def list_property():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        location = request.form.get("location", "").strip()
        city = request.form.get("city", "").strip()
        area = request.form.get("area", "").strip()
        stay_type = request.form.get("stay_type", "").strip()
        gender = request.form.get("gender", "").strip()
        price = request.form.get("price", "").strip()
        facilities = request.form.get("facilities", "").strip()
        image_url = request.form.get("image_url", "").strip()

        required = [title, location, city, area, stay_type, gender, price, facilities]
        if not all(required):
            return render_template("list_property.html", error="Please fill in all required fields.", user=session.get("user_name"))

        if stay_type not in {"PG", "Hostel", "Flat"}:
            return render_template("list_property.html", error="Stay type must be PG, Hostel or Flat.", user=session.get("user_name"))

        if gender not in {"Male", "Female", "Any"}:
            return render_template("list_property.html", error="Gender must be Male, Female or Any.", user=session.get("user_name"))

        try:
            price_value = int(price)
        except ValueError:
            return render_template("list_property.html", error="Price must be a number.", user=session.get("user_name"))

        if price_value <= 0:
            return render_template("list_property.html", error="Price must be greater than zero.", user=session.get("user_name"))

        conn = get_db()
        cur = conn.execute(
            """
            INSERT INTO listings (title, location, city, area, stay_type, gender, price, facilities, image_url, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, location, city, area, stay_type, gender, price_value, facilities, image_url, session["user_id"]),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return redirect(url_for("listing_detail", listing_id=new_id))

    return render_template("list_property.html", user=session.get("user_name"))


@app.route("/api/listings")
def api_listings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM listings").fetchall()
    conn.close()
    return jsonify([row_to_listing(row) for row in rows])


@app.route("/api/contact-messages")
@login_required
def api_contact_messages():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT contact_messages.*, listings.title AS listing_title
        FROM contact_messages
        LEFT JOIN listings ON listings.id = contact_messages.listing_id
        WHERE contact_messages.user_id=?
        ORDER BY contact_messages.created_at DESC
        """,
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


init_db()


if __name__ == "__main__":
    print("RoomRadar DB initialized")
    print("Running at http://127.0.0.1:5000")
    app.run(debug=True)
