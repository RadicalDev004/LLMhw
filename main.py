from __init__ import create_app
import os
from flask import Flask, request, redirect, make_response
from Database.chat_db import Chats
from Database.user_db import User

app = create_app()

Chats.init_db()
User.init_db()

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def handle_request(path):
    full_path = "/" + path

    if full_path.startswith('/api') or full_path.startswith('/static'):
        return f"Page not found: {full_path} <br> <a href = '/home/index'>Go to Home</a>", 404

    with open("templates/page.html", 'r', encoding='utf-8') as f:
            html = f.read()

    with open("templates/auth.html", 'r', encoding='utf-8') as f:
            html2 = f.read()
        
    if request.cookies.get('username') is None:
         return html2

    return html.replace('{{username}}', request.cookies.get('username', 'Guest'))


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(host="0.0.0.0", port = int(os.environ.get("PORT", 5000)), debug = True)