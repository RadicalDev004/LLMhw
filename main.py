from __init__ import create_app
from flask import Flask, request, redirect, make_response

app = create_app()

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def handle_request(path):
    full_path = "/" + path

    if full_path.startswith('/api') or full_path.startswith('/static'):
        return f"Page not found: {full_path} <br> <a href = '/home/index'>Go to Home</a>", 404
    return "HELOOOO"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port = int(os.environ.get("PORT", 5000)), debug = True)