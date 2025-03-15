from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import mistralai
import googlemaps
from googlemaps.places import places_nearby

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

app = Flask(__name__)
CORS(app)

@app.route('/triage', methods=['POST'])
def triage():
    try:
        data = request.json
        symptoms = data.get("symptoms", "").strip()
        age = data.get("age", "").strip()
        history = data.get("history", "").strip()

        if not symptoms or not age:
            return jsonify({"error": "Symptoms and age are required"}), 400

        # Mistral Prompt
        prompt = f"""
        A patient reports the following symptoms: {symptoms}.
        They are {age} years old and have the following medical history: {history}.
        How urgent is their condition? Reply as if you are talking to the patient themselves.
        Reply strictly in this format:
        
        - Priority: (Floating point value from 1-10 with 1 being highest priority and 10 being lowest)
        - Reason: [Reason]
        """

        client = mistralai.Mistral(api_key=MISTRAL_API_KEY)

        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        triage_result = response.choices[0].message.content

        return jsonify({"triage_result": triage_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/nearest-hospitals', methods=['POST'])
def nearest_hospitals():
    try:
        data = request.get_json()
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is None or longitude is None:
            return jsonify({"error": "Latitude and longitude are required"}), 400

        gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

        places_result = gmaps.places_nearby(
            location=(latitude, longitude),
            radius=5000,
            type='hospital'
        )

        if not places_result.get('results'):
            return jsonify({"error": "No hospitals found nearby"}), 404

        hospitals = []
        for place in places_result['results'][:10]:
            hospital_info = {
                "name": place.get("name", "No name available"),
                "address": place.get("vicinity", "No address available"),
                "latitude": place.get("geometry", {}).get("location", {}).get("lat"),
                "longitude": place.get("geometry", {}).get("location", {}).get("lng")
            }
            hospitals.append(hospital_info)

        return jsonify({"hospitals": hospitals})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=["GET", "POST"])
def index():

    traige_result = None

    if request.method == "POST":
        symptoms = request.form.get("symptoms")
        age = request.form.get("age")
        history = request.form.get("history", "")

        if not symptoms or not age:
            return render_template("index.html", error="Symptoms and age are required")
        
        response = requests.post(
            "http://localhost:5000/triage",  # Adjust the URL if hosted elsewhere
            json={"symptoms": symptoms, "age": age, "history": history}
        )

        if response.status_code == 200:
            triage_result = response.json().get("triage_result")
        else:
            triage_result = f"Error: {response.json().get('error', 'Unknown error')}"
        
        return render_template("index.html", triage_result=triage_result)
    else:
        return render_template("index.html")




if __name__ == '__main__':
    app.run(debug=True)
