import os
import logging
import datetime
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_session import Session

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_replace_in_production")
# Set session to use filesystem instead of signed cookies
# This ensures each browser gets its own session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
Session(app)

# File for storing chat messages
CHAT_FILE = "chat.txt"

# Ensure the chat file exists
def ensure_chat_file_exists():
    """Create the chat file if it doesn't exist."""
    if not os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "w", encoding="utf-8") as f:
                f.write("--- Chat Started ---\n")
            logger.debug(f"Created new chat file: {CHAT_FILE}")
        except Exception as e:
            logger.error(f"Error creating chat file: {e}")

ensure_chat_file_exists()

@app.route("/")
def index():
    """Render the main chat page."""
    username = session.get("username", "")
    return render_template("index.html", username=username)

@app.route("/join", methods=["POST"])
def join():
    """Handle user joining the chat."""
    username = request.form.get("username", "").strip()
    
    if not username:
        flash("Please enter a valid username.", "danger")
        return redirect(url_for("index"))
    
    # Store username in session
    session["username"] = username
    
    # Log user join event
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_message = f"[{timestamp}] {username} joined the chat.\n"
    
    try:
        with open(CHAT_FILE, "a", encoding="utf-8") as file:
            file.write(system_message)
        logger.debug(f"User {username} joined the chat")
    except Exception as e:
        logger.error(f"Error saving join message: {e}")
    
    return redirect(url_for("index"))

@app.route("/leave", methods=["POST"])
def leave():
    """Handle user leaving the chat."""
    username = session.get("username", "")
    
    if username:
        # Log user leave event
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_message = f"[{timestamp}] {username} left the chat.\n"
        
        try:
            with open(CHAT_FILE, "a", encoding="utf-8") as file:
                file.write(system_message)
            logger.debug(f"User {username} left the chat")
        except Exception as e:
            logger.error(f"Error saving leave message: {e}")
        
        # Clear session
        session.pop("username", None)
    
    return redirect(url_for("index"))

@app.route("/send", methods=["POST"])
def send_message():
    """Handle sending a new message."""
    username = session.get("username", "")
    message = request.form.get("message", "").strip()
    
    if not username:
        return jsonify({"status": "error", "message": "You must join the chat first"}), 401
    
    if not message:
        return jsonify({"status": "error", "message": "Message cannot be empty"}), 400
    
    # Add timestamp to the message
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {username}: {message}\n"
    
    try:
        with open(CHAT_FILE, "a", encoding="utf-8") as file:
            file.write(formatted_message)
        logger.debug(f"Message saved from {username}: {message}")
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        return jsonify({"status": "error", "message": "Failed to save message"}), 500

@app.route("/messages")
def get_messages():
    """Retrieve all chat messages."""
    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as file:
            messages = file.readlines()
        return jsonify({"messages": messages})
    except Exception as e:
        logger.error(f"Error reading messages: {e}")
        return jsonify({"status": "error", "message": "Failed to retrieve messages"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
