from flask import Flask, request, jsonify, render_template
import joblib
import requests
import os
from flasgger import Swagger
from uuid import uuid4

print("Current working directory:", os.getcwd())
print("Files in current directory:", os.listdir())

app = Flask(__name__)

# Swagger configuration to explicitly include all routes
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # include all endpoints
            "model_filter": lambda tag: True,  # include all models
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, config=swagger_config)

# Load your trained model
model = joblib.load('airquality.joblib')
print("Loaded model type:", type(model))

# OpenWeather API Key
API_KEY = 'Enter Your API Key'

# In-memory storage for AQI records (for API CRUD)
aqi_records = {}

# ========== Original Web UI Routes ==========

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/heatmap')
def heatmap():
    return render_template('heatmap.html')

@app.route('/predict_manually', methods=['POST','GET'])
def predict_manually():
    if request.method == 'POST':
        # Extract data from form
        pm25 = float(request.form['PM2.5'])
        pm10 = float(request.form['PM10'])
        o3 = float(request.form['O3'])
        no2 = float(request.form['NO2'])
        co = float(request.form['CO'])
        so2 = float(request.form['SO2'])

        # Prepare data for prediction
        sample = [[pm25, pm10, o3, no2, co, so2]]
        prediction = model.predict(sample)[0]

        # Determine Air Quality Index based on prediction
        result, conclusion = determine_air_quality(prediction)

        # Return the result to the user
        return render_template('results.html', prediction=prediction, result=result, conclusion=conclusion)
    else:
        return render_template('index.html')

@app.route('/predict_automatically', methods=['GET', 'POST'])
def predict_automatically():
    if request.method == 'POST':
        city_name = request.form.get('city_name')
        if not city_name:
            error_message = "Missing city name parameter"
            error_code = 400
            return render_template('error.html', error=error_message ,error_code=error_code), 400

        # Geocoding API to get lat and lon from city name
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
        geocode_response = requests.get(geocode_url)
        if geocode_response.status_code != 200:
            error_message = "Failed to fetch location data"
            error_code = 500
            return render_template('error.html', error=error_message ,error_code=error_code), 500
        
        geocode_data = geocode_response.json()
        if not geocode_data:
            error_message = "City not found"
            error_code = 404
            return render_template('error.html', error=error_message ,error_code=error_code), 404

        # Assuming the first result is the most relevant
        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']

        # Now use lat and lon to get air pollution data
        air_quality_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        air_quality_response = requests.get(air_quality_url)
        if air_quality_response.status_code != 200:
            error_message = "Failed to fetch Air Quality Index data"
            error_code = 500
            return render_template('error.html', error=error_message ,error_code=error_code), 500

        air_quality_data = air_quality_response.json()['list'][0]['components']
        sample = [
            [air_quality_data['pm2_5'], air_quality_data['pm10'], air_quality_data['o3'],
             air_quality_data['no2'], air_quality_data['co'], air_quality_data['so2']]
        ]
        prediction = round(model.predict(sample)[0],2)

        result, conclusion = determine_air_quality(prediction)

        return render_template('results.html', prediction=prediction, result=result, conclusion=conclusion)

    else:
        return render_template('city.html')

def determine_air_quality(prediction):
    if prediction < 50:
        return 'Air Quality Index is Good', 'The Air Quality Index is excellent. It poses little or no risk to human health.'
    elif 51 <= prediction < 100:
        return 'Air Quality Index is Satisfactory', 'The Air Quality Index is satisfactory, but there may be a risk for sensitive individuals.'
    elif 101 <= prediction < 200:
        return 'Air Quality Index is Moderately Polluted', 'Moderate health risk for sensitive individuals.'
    elif 201 <= prediction < 300:
        return 'Air Quality Index is Poor', 'Health warnings of emergency conditions.'
    elif 301 <= prediction < 400:
        return 'Air Quality Index is Very Poor', 'Health alert: everyone may experience more serious health effects.'
    else:
        return 'Air Quality Index is Severe', 'Health warnings of emergency conditions. The entire population is more likely to be affected.'

# ========== Helper Validation Function ==========

def validate_aqi_data(data):
    required_fields = ['pm25', 'pm10', 'o3', 'no2', 'co', 'so2']
    for field in required_fields:
        if field not in data:
            return False
        try:
            float(data[field])
        except (ValueError, TypeError):
            return False
    return True

# ========== REST API CRUD Endpoints with Swagger Specs ==========

@app.route('/api/records', methods=['GET'])
def get_records():
    """
    Get all AQI records
    ---
    responses:
      200:
        description: A list of all AQI records
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    example: "123e4567-e89b-12d3-a456-426614174000"
                  pm25:
                    type: number
                    example: 12.5
                  pm10:
                    type: number
                    example: 20.1
                  o3:
                    type: number
                    example: 0.03
                  no2:
                    type: number
                    example: 0.01
                  co:
                    type: number
                    example: 0.4
                  so2:
                    type: number
                    example: 0.005
    """
    return jsonify(list(aqi_records.values()))

@app.route('/api/records', methods=['POST'])
def create_record():
    """
    Create a new AQI record
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [pm25, pm10, o3, no2, co, so2]
            properties:
              pm25:
                type: number
                example: 12.5
              pm10:
                type: number
                example: 20.1
              o3:
                type: number
                example: 0.03
              no2:
                type: number
                example: 0.01
              co:
                type: number
                example: 0.4
              so2:
                type: number
                example: 0.005
    responses:
      201:
        description: AQI record created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: string
                  example: "123e4567-e89b-12d3-a456-426614174000"
                pm25:
                  type: number
                  example: 12.5
                pm10:
                  type: number
                  example: 20.1
                o3:
                  type: number
                  example: 0.03
                no2:
                  type: number
                  example: 0.01
                co:
                  type: number
                  example: 0.4
                so2:
                  type: number
                  example: 0.005
      400:
        description: Invalid input data
    """
    data = request.json
    if not data or not validate_aqi_data(data):
        return jsonify({'error': 'Invalid input data'}), 400
    record_id = str(uuid4())
    aqi_records[record_id] = {"id": record_id, **data}
    return jsonify(aqi_records[record_id]), 201

@app.route('/api/records/<record_id>', methods=['GET'])
def get_record(record_id):
    """
    Get a specific AQI record by ID
    ---
    parameters:
      - in: path
        name: record_id
        schema:
          type: string
        required: true
        description: The ID of the AQI record
    responses:
      200:
        description: AQI record found
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: string
                  example: "123e4567-e89b-12d3-a456-426614174000"
                pm25:
                  type: number
                  example: 12.5
                pm10:
                  type: number
                  example: 20.1
                o3:
                  type: number
                  example: 0.03
                no2:
                  type: number
                  example: 0.01
                co:
                  type: number
                  example: 0.4
                so2:
                  type: number
                  example: 0.005
      404:
        description: Record not found
    """
    if record_id not in aqi_records:
        return jsonify({'error': 'Record not found'}), 404
    return jsonify(aqi_records[record_id])

@app.route('/api/records/<record_id>', methods=['PUT'])
def update_record(record_id):
    """
    Update an existing AQI record by ID
    ---
    parameters:
      - in: path
        name: record_id
        schema:
          type: string
        required: true
        description: The ID of the AQI record
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [pm25, pm10, o3, no2, co, so2]
            properties:
              pm25:
                type: number
                example: 12.5
              pm10:
                type: number
                example: 20.1
              o3:
                type: number
                example: 0.03
              no2:
                type: number
                example: 0.01
              co:
                type: number
                example: 0.4
              so2:
                type: number
                example: 0.005
    responses:
      200:
        description: AQI record updated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: string
                  example: "123e4567-e89b-12d3-a456-426614174000"
                pm25:
                  type: number
                  example: 12.5
                pm10:
                  type: number
                  example: 20.1
                o3:
                  type: number
                  example: 0.03
                no2:
                  type: number
                  example: 0.01
                co:
                  type: number
                  example: 0.4
                so2:
                  type: number
                  example: 0.005
      400:
        description: Invalid input data
      404:
        description: Record not found
    """
    if record_id not in aqi_records:
        return jsonify({'error': 'Record not found'}), 404
    data = request.json
    if not data or not validate_aqi_data(data):
        return jsonify({'error': 'Invalid input data'}), 400
    aqi_records[record_id].update(data)
    return jsonify(aqi_records[record_id])

@app.route('/api/records/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    """
    Delete an AQI record by ID
    ---
    parameters:
      - in: path
        name: record_id
        schema:
          type: string
        required: true
        description: The ID of the AQI record to delete
    responses:
      204:
        description: Record deleted successfully
      404:
        description: Record not found
    """
    if record_id not in aqi_records:
        return jsonify({'error': 'Record not found'}), 404
    del aqi_records[record_id]
    return '', 204

@app.route('/api/records/reset', methods=['POST'])
def reset_records():
    """
    Reset (clear) all AQI records
    ---
    responses:
      204:
        description: All records cleared successfully
    """
    aqi_records.clear()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
