from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# ---------------- ROOT (FORCE LOGIN EVERY TIME) ----------------
@app.route("/")
def home():
    session.clear()   # 🔥 always logout on visit
    return redirect("/login")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]

    tasks = Task.query.filter_by(user_id=uid).all()

    total = len(tasks)
    completed = len([t for t in tasks if t.completed])
    pending = total - completed

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending
    )


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "Username already exists"

        user = User(
            username=username,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- ADD TASK ----------------
@app.route("/add", methods=["POST"])
def add():

    if "user_id" not in session:
        return redirect("/login")

    content = request.form["content"]

    if content.strip() == "":
        return redirect("/dashboard")

    task = Task(content=content, user_id=session["user_id"])

    db.session.add(task)
    db.session.commit()

    return redirect("/dashboard")


# ---------------- COMPLETE TASK ----------------
@app.route("/complete/<int:id>")
def complete(id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    if task.user_id != session["user_id"]:
        return "Unauthorized"

    task.completed = not task.completed
    db.session.commit()

    return redirect("/dashboard")


# ---------------- DELETE TASK ----------------
@app.route("/delete/<int:id>")
def delete(id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    if task.user_id != session["user_id"]:
        return "Unauthorized"

    db.session.delete(task)
    db.session.commit()

    return redirect("/dashboard")


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)