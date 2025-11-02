from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"  # заміни на свій довгий ключ

# --- Параметри Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Функції роботи з постами ---
def get_posts():
    response = supabase.table("posts").select("*").execute()
    return response.data

def add_post(title, content, author):
    supabase.table("posts").insert({"title": title, "content": content, "author": author}).execute()

# --- Головна сторінка ---
@app.route("/")
def index():
    posts = get_posts()
    user = session.get("user")
    return render_template("index.html", posts=posts, user=user)

# --- Реєстрація ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Перевірка чи існує користувач
        existing = supabase.table("users").select("*").eq("username", username).execute()
        if existing.data:
            flash("❌ Користувач вже існує")
            return redirect(url_for("register"))

        supabase.table("users").insert({"username": username, "password": password}).execute()
        flash("✅ Реєстрація успішна, увійдіть у систему")
        return redirect(url_for("login"))

    return render_template("register.html")

# --- Логін ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        if user.data:
            session["user"] = username
            flash("✅ Вхід виконано")
            return redirect(url_for("index"))
        else:
            flash("❌ Невірний логін або пароль")

    return render_template("login.html")

# --- Вихід ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Ви вийшли з акаунту")
    return redirect(url_for("login"))

# --- Додати пост ---
@app.route("/add_post", methods=["GET", "POST"])
def add_post_route():
    user = session.get("user")
    if not user:
        flash("❌ Вхід обов’язковий")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        add_post(title, content, user)
        flash("✅ Пост додано")
        return redirect(url_for("index"))

    return render_template("add_post.html", user=user)

# --- Запуск ---
if __name__ == "__main__":
    app.run(debug=True)
