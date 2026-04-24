from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
import requests
import os
from groq import Groq

app = Flask(__name__)
app.secret_key = "secret123"

# ======================
# WEATHER API
# ======================
WEATHER_API = "f838ccb51099617f6ce5f3400e986097"

# ======================
# GROQ AI CLIENT
# ======================
groq_client = Groq(api_key="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")

# ======================
# DATABASE CONNECTION
# ======================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sahil@29",
    database="agriculture"
)

# ======================
# HOME
# ======================
@app.route('/')
def home():
    return render_template("index.html")


# ======================
# LOGIN
# ======================
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


# ======================
# REGISTER
# ======================
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


# ======================
# DASHBOARD
# ======================
@app.route('/dashboard')
def dashboard():

    if 'username' not in session:
        return redirect('/login')

    return render_template("dashboard.html", username=session['username'])


# ======================
# PROFILE
# ======================
@app.route('/profile')
def profile():

    if 'username' not in session:
        return redirect('/login')

    return render_template("profile.html", username=session['username'])


# ======================
# LOGOUT
# ======================
@app.route('/logout')
def logout():

    session.pop('username', None)

    return redirect('/login')


# ======================
# CROP PAGE
# ======================
@app.route('/crop')
def crop():

    if 'username' not in session:
        return redirect('/login')

    return render_template("crop.html")


# ======================
# CONTACT / ABOUT
# ======================
@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/about')
def about():
    return render_template("about.html")


# ======================
# CROP RECOMMENDATION
# ======================
@app.route('/recommend', methods=['POST'])
def recommend():

    soil = request.form['soil']
    location = request.form['location']

    cursor = db.cursor()

    query = """
    SELECT crop_name, market_price
    FROM crops
    WHERE soil_type=%s
    ORDER BY market_price DESC
    LIMIT 3
    """

    cursor.execute(query,(soil,))
    crops = cursor.fetchall()

    # WEATHER API
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location},IN&appid={WEATHER_API}&units=metric"

    try:
        response = requests.get(url)
        weather_data = response.json()

        if "main" in weather_data:
            temperature = weather_data["main"]["temp"]
            weather = weather_data["weather"][0]["description"]
        else:
            temperature = "Not available"
            weather = "Weather unavailable"

    except:
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


# ======================
# GROQ FARMER CHATBOT
# ======================
def ask_chatbot(question):

    try:

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are an agriculture expert helping farmers with crops, fertilizers, irrigation, and plant diseases. Give short practical answers."
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Groq Error:", e)
        return "AI service temporarily unavailable."


@app.route('/chatbot', methods=['POST'])
def chatbot():

    if 'username' not in session:
        return redirect('/login')

    question = request.form['question']
    answer = ask_chatbot(question)

    return render_template(
        "dashboard.html",
        username=session['username'],
        reply=answer
    )


# ======================
# PLANT DISEASE DETECTOR
# ======================
@app.route('/detect', methods=['POST'])
def detect():

    image = request.files['image']

    if image.filename == "":
        return "No image uploaded"

    upload_folder = "static/uploads"

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filepath = os.path.join(upload_folder, image.filename)
    image.save(filepath)

    # Temporary disease detection (you can improve later)
    disease = "Leaf Spot Disease"

    # Ask Groq for cure
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role":"system",
                "content":"You are an agriculture expert helping farmers treat plant diseases."
            },
            {
                "role":"user",
                "content":f"Explain the cure and prevention for {disease} in crops."
            }
        ]
    )

    cure = response.choices[0].message.content

    return render_template(
        "disease_result.html",
        disease=disease,
        cure=cure,
        image=filepath
    )

# ======================
# RUN APP
# ======================
if __name__ == "__main__":
    app.run(debug=True)