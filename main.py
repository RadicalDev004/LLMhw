from __init__ import create_app
import os, json, base64, threading, time
from flask import Flask, request, redirect, make_response, send_from_directory
from flask_sock import Sock
from websocket import create_connection
from dotenv import load_dotenv
from Database.chat_db import Chats
from Database.user_db import User
from app.rag import initialize_vectorstore, retriever

app = create_app()
sock = Sock(app)
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
Chats.init_db()
User.init_db()

SAMPLE_RATE = 16000
MIN_MS_BEFORE_COMMIT = 120           
MIN_SAMPLES = SAMPLE_RATE * MIN_MS_BEFORE_COMMIT // 1000
pending_samples = 0

@app.route('/static/<path:filename>')
def serve_static(filename):
    # serves files from ./static
    return send_from_directory('static', filename)

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

def openai_connect():
    headers = [
        f"Authorization: Bearer {OPENAI_KEY}",
        "OpenAI-Beta: realtime=v1",        # <-- required
    ]
    ws = create_connection(REALTIME_URL, header=headers)
    # tell Realtime we’ll stream 16k PCM16
    ws.send(json.dumps({
        "type": "session.update",
        "session": { 
            "input_audio_format": "pcm16" , 
            "input_audio_transcription": {"model": "gpt-4o-mini-transcribe"},
            #"turn_detection": {"type": "server_vad", "silence_duration_ms": 300},
            "turn_detection": { "type": "server_vad", "silence_duration_ms": 300 }
        }
    }))
    return ws

@sock.route("/stt")
def stt(client_ws):
    upstream = openai_connect()
    stop = False

    # OpenAI -> Browser: only transcripts
    def pump_down():
        nonlocal stop
        try:
            while not stop:
                evt = json.loads(upstream.recv())
                t = (evt.get("type") or "").strip()

                if t == "conversation.item.input_audio_transcription.delta":
                    client_ws.send(json.dumps({
                        "type": "transcript.partial",
                        "text": evt.get("delta", "")
                    }))

                elif t == "conversation.item.input_audio_transcription.completed":
                    client_ws.send(json.dumps({
                        "type": "transcript.final",
                        "text": evt.get("transcript", "")
                    }))

                elif t.endswith(".failed") or t == "error":
                    # surfaces issues like language/model config, etc.
                    print("Transcription error:", evt)

                # Ignore any response.* events; we never send response.create
        except Exception:
            pass

    threading.Thread(target=pump_down, daemon=True).start()

    # Browser -> OpenAI: just append audio frames; DO NOT commit
    try:
        while True:
            data = client_ws.receive()
            if data is None:
                break
            if isinstance(data, bytes):
                upstream.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": base64.b64encode(data).decode("ascii")
                }))
            else:
                # ignore text like heartbeats
                pass
    except Exception:
        pass
    finally:
        stop = True
        try: upstream.close()
        except: pass


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(host="0.0.0.0", port = int(os.environ.get("PORT", 5000)), debug = True)
    print("Starting the application...")
    retriever = initialize_vectorstore()
    