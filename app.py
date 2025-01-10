from flask import Flask, render_template, request, jsonify
import sqlite3
import requests
# Import sensor_reader.py for live weather readings

app = Flask(__name__)

# Database Paths
CITIES_DB_PATH = r"C:\Users\Acer\PycharmProjects\weatherstation\cities.db"
WEATHER_DB_PATH = r"C:\Users\Acer\PycharmProjects\weatherstation\weather_data.db"

# OpenWeatherMap API settings
API_KEY = "e5780636d5621aebf17df75fe667b8a7"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"


# Fetch weather data for a city
def fetch_weather_data(city):
    response = requests.get(BASE_URL, params={"q": city, "appid": API_KEY, "units": "metric"})
    data = response.json()
    if data["cod"] == 200:
        return {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"].capitalize(),
            "wind_speed": data["wind"]["speed"]
        }
    else:
        return {"error": "City not found or API error"}


# Log weather data to the database
def log_weather_to_db(city, weather):
    if "error" in weather:
        return
    conn = sqlite3.connect(WEATHER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO weather (city, temperature, humidity, wind_speed, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (city, weather["temperature"], weather["humidity"], weather["wind_speed"], weather["description"]))
    conn.commit()
    conn.close()


# Fetch weather history from the database
def fetch_weather_history(city):
    conn = sqlite3.connect(WEATHER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT temperature, humidity, wind_speed, description, timestamp
        FROM weather WHERE city = ?
        ORDER BY timestamp DESC LIMIT 10
    ''', (city,))
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/search_cities')
def search_cities():
    query = request.args.get('q', '').lower()
    conn = sqlite3.connect(CITIES_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM cities WHERE name LIKE ?', (f'{query}%',))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)


@app.route('/weather')
def get_weather():
    city = request.args.get('city')
    weather = fetch_weather_data(city)
    if "error" not in weather:
        log_weather_to_db(city, weather)
    return jsonify(weather)


@app.route('/history/<city>')
def history(city):
    history_data = fetch_weather_history(city)
    return render_template("city_history.html", city=city, history_data=history_data)







if __name__ == "__main__":
      # Initialize sensor database
    app.run(host="0.0.0.0", port=5000, debug=True)
