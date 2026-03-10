from flask import Flask, render_template, request, redirect, session
import mysql.connector
import requests

app = Flask(__name__)

app.secret_key = "secret123"

API_KEY = "f838ccb51099617f6ce5f3400e986097"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sahil@29",
    database="agriculture"
)

# HOME
@app.route('/')
def home():
    return render_template("index.html")


# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template("login.html", error="Please enter username and password")

        cursor = db.cursor()

        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(query,(username,password))

        user = cursor.fetchone()

        if user:
            session['username'] = username
            return redirect('/dashboard')

        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# REGISTER
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()

        query = "INSERT INTO users(name,username,password) VALUES(%s,%s,%s)"
        cursor.execute(query,(name,username,password))

        db.commit()

        return redirect('/login')

    return render_template("register.html")


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'username' not in session:
        return redirect('/login')

    return render_template("dashboard.html", username=session['username'])


# PROFILE
@app.route('/profile')
def profile():

    if 'username' not in session:
        return redirect('/login')

    return render_template("profile.html", username=session['username'])


# LOGOUT
@app.route('/logout')
def logout():

    session.pop('username', None)

    return redirect('/login')


# CROP PAGE
@app.route('/crop')
def crop():

    if 'username' not in session:
        return redirect('/login')

    return render_template("crop.html")


# CONTACT
@app.route('/contact')
def contact():
    return render_template("contact.html")


# ABOUT
@app.route('/about')
def about():
    return render_template("about.html")


# CROP RECOMMENDATION
@app.route('/recommend', methods=['POST'])
def recommend():

    soil = request.form['soil']
    location = request.form['location']

    cursor = db.cursor()

    query = "SELECT crop_name, market_price FROM crops WHERE soil_type=%s LIMIT 3"
    cursor.execute(query,(soil,))
    crops = cursor.fetchall()

    url = f"https://api.openweathermap.org/data/2.5/weather?q={location},IN&appid={API_KEY}&units=metric"

    response = requests.get(url)
    weather_data = response.json()

    if "main" in weather_data:
        temperature = weather_data["main"]["temp"]
        weather = weather_data["weather"][0]["description"]
    else:
        temperature = "Not available"
        weather = "Weather unavailable"

    fertilizer = ""

    if soil == "Black":
        fertilizer = "Urea and DAP fertilizer"

    elif soil == "Red":
        fertilizer = "Nitrogen and Phosphorus fertilizer"

    elif soil == "Sandy":
        fertilizer = "Organic compost and Potassium fertilizer"

    elif soil == "Laterite":
        fertilizer = "NPK fertilizer and compost"

    return render_template(
        "result.html",
        crops=crops,
        location=location,
        temperature=temperature,
        weather=weather,
        fertilizer=fertilizer
    )


if __name__ == "__main__":
    app.run(debug=True)