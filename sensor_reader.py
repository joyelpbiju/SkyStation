import smbus2
import bme280
import sqlite3
import os
from flask import Flask, render_template, jsonify

# Flask app initialization
app = Flask(__name__)

# Database file path
DB_PATH = "sensor_readings.db"

# BME280 sensor I2C address
BME280_ADDRESS = 0x76  # Default I2C address for the BME280 sensor


# Initialize the database
def initialize_database():
    """Create the SQLite database if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL NOT NULL,
                pressure REAL NOT NULL,
                humidity REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print(f"Database '{DB_PATH}' initialized successfully.")


# Read sensor data
def read_sensor_data():
    """
    Read data from the BME280 sensor.
    Returns a dictionary with temperature, pressure, and humidity or an error message.
    """
    try:
        bus = smbus2.SMBus(1)  # Initialize I2C bus
        calibration_params = bme280.load_calibration_params(bus, BME280_ADDRESS)
        data = bme280.sample(bus, BME280_ADDRESS, calibration_params)
        return {
            "temperature": round(data.temperature, 2),
            "pressure": round(data.pressure, 2),
            "humidity": round(data.humidity, 2),
            "error": None
        }
    except Exception as e:
        return {"error": str(e)}


# Save sensor data to the database
def save_sensor_data_to_db(data):
    """
    Save sensor data to the SQLite database.
    Expects a dictionary with temperature, pressure, and humidity.
    """
    if data["error"]:
        print(f"Error reading sensor: {data['error']}")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_readings (temperature, pressure, humidity)
            VALUES (?, ?, ?)
        ''', (data["temperature"], data["pressure"], data["humidity"]))
        conn.commit()
        conn.close()
        print("Sensor data saved to database successfully.")
    except Exception as e:
        print(f"Error saving data to database: {e}")


# Flask route to view all sensor readings
@app.route('/view_history/sensor')
def view_sensor_history():
    """
    Fetch all sensor readings from the database and display them in a table.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, temperature, pressure, humidity, timestamp
            FROM sensor_readings
            ORDER BY timestamp DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return render_template('sensor_history.html', readings=rows)
    except Exception as e:
        return jsonify({"error": f"Error fetching sensor history: {e}"})


# Main function to initialize the database and save data
def main():
    """
    Initialize the database, read data from the sensor, and save it to the database.
    """
    initialize_database()
    sensor_data = read_sensor_data()
    if sensor_data["error"]:
        print(f"Error reading sensor: {sensor_data['error']}")
    else:
        print(f"Sensor Data: Temperature={sensor_data['temperature']} °C, "
              f"Pressure={sensor_data['pressure']} hPa, "
              f"Humidity={sensor_data['humidity']} %")
        save_sensor_data_to_db(sensor_data)


if __name__ == "__main__":
    # Run the main function to read and save data
    initialize_database()
    main()
    # Start the Flask app to view history
    app.run(host="0.0.0.0", port=5001, debug=True)
