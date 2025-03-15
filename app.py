from flask import Flask, request, jsonify
from flask_cors import CORS
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
    

@app.route('/nearest_hospitals', methods=['GET'])
def nearest_hospitals():
    try:
        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)

        if not latitude or not longitude:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

        places_result = places_nearby(
            gmaps,
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

if __name__ == '__main__':
    app.run(debug=True)
