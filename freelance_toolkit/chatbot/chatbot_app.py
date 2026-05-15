from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a helpful business assistant. 
You answer questions clearly and professionally.
Keep responses concise and friendly."""

conversation_history = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    conversation_history.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[-10:],
        max_tokens=500,
        temperature=0.7
    )

    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)