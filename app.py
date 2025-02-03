from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/chat', methods = ['POST'])
def chat(): 
    user_input = request.json.get("message")
    response = {"reply": f"Echo: {user_input}"}
    return jsonify(response)

if __name__ == "__main__":
    print("Starting the Flask app...")
    app.run(host = '127.0.0.1', port = 5000)
