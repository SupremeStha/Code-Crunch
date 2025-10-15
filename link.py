from flask import Flask, request, jsonify
from flask_cors import CORS
from chatbot import MentalHealthChatbot

app = Flask(__name__)
CORS(app)

bot = MentalHealthChatbot()

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message", "")
        if not message:
            return jsonify({"reply": "Please enter a message."})
        
        response = bot.get_response(message)
        return jsonify({"reply": response})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
