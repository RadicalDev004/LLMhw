from flask import Flask
from API.chat import chat

def create_app():
    app = Flask(__name__)
    app.register_blueprint(chat)
    return app
