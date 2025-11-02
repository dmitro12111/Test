from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"  # заміни на свій випадковий довгий ключ

# --- 1. Параметри Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Отримати всі пости ---
def get_posts():
    response = supabase.table("posts").select("*").execute()
    return response.data

# --- Додати пост ---
def add_post(title, content, author):
    supabase.table("posts").insert({"title": title, "content": content, "author": author}).execute()

# --- Реєстрація ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # перевірка чи вже є такий користувач
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

# --- Головна сторінка ---
@app.route("/")
def index():
    posts = get_posts()
    user = session.get("user")
    # print(user)
    # print(posts)
    return render_template("index.html", posts=posts, user=user)

# --- Роут для створення поста ---
@app.route('/add-post', methods=['GET', 'POST'])
def add_post_route():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author = session.get('user')

        if not author:
            flash("Автор не визначений. Увійдіть у систему.")
            return redirect(url_for('login'))

        if not title or not content:
            flash("Заповніть усі поля.")
            return redirect(url_for('add_post_route'))

        # Вставляємо пост у таблицю "posts"
        data = {
            "title": title,
            "content": content,
            "author": author
        }
        response = supabase.table("posts").insert(data).execute()

        if response.data:
            flash("Пост успішно створено!")
            return redirect(url_for('index'))
        else:
            flash("Помилка при створенні поста.")
            return redirect(url_for('add_post_route'))

    # GET — показує форму
    return render_template('add_post.html')
# --- Редагування поста ---
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    user = session.get("user")
    if not user:
        flash("Увійдіть у систему, щоб редагувати пости.")
        return redirect(url_for('login'))

    # Отримуємо пост за ID
    response = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not response.data:
        flash("Пост не знайдено.")
        return redirect(url_for('index'))

    post = response.data[0]

    # Перевірка автора
    if post["author"] != user:
        flash("❌ Ви не можете редагувати чужий пост.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_title = request.form.get("title")
        new_content = request.form.get("content")

        if not new_title or not new_content:
            flash("Заповніть усі поля.")
            return redirect(url_for('edit_post', post_id=post_id))

        supabase.table("posts").update({
            "title": new_title,
            "content": new_content
        }).eq("id", post_id).execute()

        flash("✅ Пост оновлено!")
        return redirect(url_for('index'))

    return render_template("edit_post.html", post=post)


# --- Видалення поста ---
@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    user = session.get("user")
    if not user:
        flash("Спершу увійдіть у систему.")
        return redirect(url_for('login'))

    response = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not response.data:
        flash("Пост не знайдено.")
        return redirect(url_for('index'))

    post = response.data[0]
    if post["author"] != user:
        flash("❌ Ви не можете видаляти чужі пости.")
        return redirect(url_for('index'))

    supabase.table("posts").delete().eq("id", post_id).execute()
    flash("🗑️ Пост видалено.")
    return redirect(url_for('index'))


# --- 9. Запуск ---
if __name__ == "__main__":
    app.run(debug=True)
