
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("foodie.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                category TEXT NOT NULL,
                address TEXT DEFAULT '',
                price TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                rating INTEGER DEFAULT 0,
                visited INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM restaurants"
        ).fetchone()[0]

        if count == 0:
            samples = [
                (
                    "巷弄咖啡",
                    "台北",
                    "咖啡廳",
                    "大安區",
                    "$$",
                    "適合週末午後來坐坐",
                    4,
                    1
                ),
                (
                    "日和食堂",
                    "台中",
                    "日式料理",
                    "西區",
                    "$$",
                    "下次想試試其他餐點",
                    0,
                    0
                ),
                (
                    "小島甜點",
                    "高雄",
                    "甜點",
                    "鹽埕區",
                    "$",
                    "想找時間再訪",
                    5,
                    1
                )
            ]

            conn.executemany("""
                INSERT INTO restaurants
                (name, city, category, address, price, notes, rating, visited)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, samples)


@app.route("/")
def index():
    keyword = request.args.get("keyword", "").strip()
    city = request.args.get("city", "").strip()
    category = request.args.get("category", "").strip()
    visited = request.args.get("visited", "")

    sql = "SELECT * FROM restaurants WHERE 1=1"
    params = []

    if keyword:
        sql += """
            AND (
                name LIKE ?
                OR address LIKE ?
                OR notes LIKE ?
            )
        """
        term = f"%{keyword}%"
        params.extend([term, term, term])

    if city:
        sql += " AND city = ?"
        params.append(city)

    if category:
        sql += " AND category = ?"
        params.append(category)

    if visited in ("0", "1"):
        sql += " AND visited = ?"
        params.append(int(visited))

    sql += " ORDER BY created_at DESC, id DESC"

    with get_db() as conn:
        restaurants = conn.execute(sql, params).fetchall()

        cities = [
            row["city"]
            for row in conn.execute(
                "SELECT DISTINCT city FROM restaurants ORDER BY city"
            ).fetchall()
        ]

        categories = [
            row["category"]
            for row in conn.execute(
                "SELECT DISTINCT category FROM restaurants ORDER BY category"
            ).fetchall()
        ]

        total = conn.execute(
            "SELECT COUNT(*) FROM restaurants"
        ).fetchone()[0]

        visited_count = conn.execute(
            "SELECT COUNT(*) FROM restaurants WHERE visited = 1"
        ).fetchone()[0]

    return render_template(
        "index.html",
        restaurants=restaurants,
        cities=cities,
        categories=categories,
        keyword=keyword,
        selected_city=city,
        selected_category=category,
        selected_visited=visited,
        total=total,
        visited_count=visited_count
    )


@app.route("/add", methods=["POST"])
def add_restaurant():
    name = request.form.get("name", "").strip()
    city = request.form.get("city", "").strip()
    category = request.form.get("category", "").strip()
    address = request.form.get("address", "").strip()
    price = request.form.get("price", "").strip()
    notes = request.form.get("notes", "").strip()

    if name and city and category:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO restaurants
                (name, city, category, address, price, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, city, category, address, price, notes))

    return redirect(url_for("index"))


@app.route("/toggle/<int:restaurant_id>", methods=["POST"])
def toggle_visited(restaurant_id):
    with get_db() as conn:
        conn.execute("""
            UPDATE restaurants
            SET visited = CASE WHEN visited = 1 THEN 0 ELSE 1 END
            WHERE id = ?
        """, (restaurant_id,))

    return redirect(url_for("index"))


@app.route("/edit/<int:restaurant_id>", methods=["POST"])
def edit_restaurant(restaurant_id):
    name = request.form.get("name", "").strip()
    city = request.form.get("city", "").strip()
    category = request.form.get("category", "").strip()
    address = request.form.get("address", "").strip()
    price = request.form.get("price", "").strip()
    notes = request.form.get("notes", "").strip()
    rating = request.form.get("rating", "0")

    try:
        rating = max(0, min(5, int(rating)))
    except ValueError:
        rating = 0

    if name and city and category:
        with get_db() as conn:
            conn.execute("""
                UPDATE restaurants
                SET name = ?, city = ?, category = ?, address = ?,
                    price = ?, notes = ?, rating = ?
                WHERE id = ?
            """, (
                name, city, category, address, price,
                notes, rating, restaurant_id
            ))

    return redirect(url_for("index"))


@app.route("/delete/<int:restaurant_id>", methods=["POST"])
def delete_restaurant(restaurant_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM restaurants WHERE id = ?",
            (restaurant_id,)
        )

    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
