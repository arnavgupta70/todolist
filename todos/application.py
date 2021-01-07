import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///list.db")
#####################################################################################################################################################
@app.route("/")
@login_required
def index():
    """Displays all tasks to user"""

    # Query on the database with information about "users" currently owned stocks
    rows = db.execute("SELECT * FROM incomplete_tasks WHERE user_id = :user", user=session["user_id"])

    # Creates a blank table, "stocks"
    tasks = []

    # Iterate over every row in "rows"
    for index, row in enumerate(rows):

        # Append to the list, "tasks" the information about "Task Name", "Start Date" and "End Date"
        tasks.append(list((row['task_name'], row['start_date'], row['end_date'])))

    # Redirect to "index.html"
    return render_template("index.html", stocks=tasks)
#####################################################################################################################################################
@app.route("/updatetasks", methods=["GET", "POST"])
@login_required
def update():
    """Allows usert to set the task to complete"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Access the symbol of company
        symbol = request.form.get("task")

        if not symbol:
            return apology("please specify which task you have completed")

        else:
            db.execute("INSERT INTO completed_tasks(user_id, task_name, start_date) SELECT user_id, task_name, start_date FROM incomplete_tasks WHERE user_id = :user AND task_name = :task",
                        user=session["user_id"], task=symbol)

            db.execute("DELETE FROM incomplete_tasks WHERE user_id = :user AND task_name = :task",
                        user=session["user_id"], task=symbol)

        # Inform user the purchase was a success
        flash("Congratulations on completing the task!")

        # Redirect user to the Homepage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Query for Database
        rows = db.execute("SELECT task_name, start_date FROM incomplete_tasks WHERE user_id = :user",
                            user=session["user_id"])

        # Creates a dictionary called "stocks"
        stocks = {}

        for row in rows:
            stocks[row["task_name"]] = row["start_date"]

        return render_template("update.html", stocks=stocks)
#####################################################################################################################################################
@app.route("/completedtasks", methods=["GET", "POST"])
@login_required
def complete():
    """Displays all completed tasks to user"""

    # Query on the database with information about "users" currently owned stocks
    rows = db.execute("SELECT * FROM completed_tasks WHERE user_id = :user", user=session["user_id"])

    # Creates a blank table, "stocks"
    tasks = []

    # Iterate over every row in "rows"
    for index, row in enumerate(rows):

        # Append to the list, "tasks" the information about "Task Name", "Start Date" and "End Date"
        tasks.append(list((row['task_name'], row['start_date'], row['end_date'])))

    # Redirect to "index.html"
    return render_template("complete.html", stocks=tasks)
#####################################################################################################################################################
@app.route("/addtasks", methods=["GET", "POST"])
@login_required
def addtasks():
    """Allow user to add tasks"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("completion"):
            return apology("missing completion date", 403)

        else:
            # Store user input for task in "task"
            task = request.form.get("tasks")

            # Store user input for completion date in "complete"
            complete = request.form.get("completion")

            # Update database
            db.execute("INSERT INTO incomplete_tasks(user_id, task_name, end_date) VALUES (:user, :todo, :date)",
                        user=session["user_id"], todo=task, date=complete)

            # Inform the user their task has been added
            flash("Task has been added!")

            # Redirect user back to Homepage
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("addtasks.html")
#####################################################################################################################################################
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
#####################################################################################################################################################
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
#####################################################################################################################################################
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # If the request method equals "POST", this means the user has clicked the Register button
    if request.method == "POST":

        # Checks if user input for Username is blank
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Checks if user input for Username is blank
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Checks if user input for Password and Confirm-Password don't match
        elif ((request.form.get("password")) != (request.form.get("confirmation"))):
            return apology("passwords don't match", 403)

        # Checks if user input for Username already exists
        elif db.execute("SELECT * FROM users WHERE username = :username",
                            username=request.form.get("username")):
            return apology("username is taken", 403)

        else:

            # Insert user and hash of the password into the table
            db.execute("INSERT INTO users(username, hash) VALUES(:username, :hash)",
                        username=request.form.get("username"),
                        hash=generate_password_hash(request.form.get("password")))

            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("username"))

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Inform the user their account has been registered
            flash("Registered!")

            # Redirect user back to Homepage
            return redirect("/")

    # When the request method equals "GET", this means the user reached route by clicking link or VIA redirect
    else:
        return render_template("register.html")
#####################################################################################################################################################
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)
#####################################################################################################################################################
# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)