from flask import Blueprint, request, jsonify
from Database.chat_db import Chats, SessionLocal
from Database.user_db import User
from records.addchat import AddChat
from records.getchat import GetChat
from records.addmessage import AddMsg
from records.getaudio import GetAudio
from records.getchatinfo import GetChatInfo
from pydantic import ValidationError
import re, json, codecs
from datetime import datetime, timezone
import traceback
import os, io, base64, tempfile
import base64
import unicodedata
from openai import OpenAI
from app.rag import create_vectorstore, retriever, initialize_vectorstore
BLOCK = "nu am suficiente informatii pentru a raspunde la aceasta intrebare"

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
_ue_re = re.compile(r'\\u[0-9a-fA-F]{4}')
chat = Blueprint('add_chat', __name__)
MEDIA_TAG_RE = re.compile(r"\[(image|audio)\](.*?)\[/\1\]", re.IGNORECASE | re.DOTALL)
client = OpenAI(api_key = OPENAI_KEY)


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_summary_by_title",
            "description": "Returns a summary of the book given its title",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the book, e.g., '1984'"
                    }
                },
                "required": ["title"]
            }
        }
    }
]
retriever = initialize_vectorstore()

@chat.route('/api/add_chat', methods=['POST'])
def add_chat():
    try:
        data = AddChat.parse_obj(request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    session = SessionLocal()
    chatId = -1
    
    try:
        chat = Chats(
            username=data.username,
            chat_name=data.chatname,
            content="",
            timestamp=datetime.utcnow()
        )

        session.add(chat)
        session.commit()
        chatId = chat.id

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        session.close()

    return jsonify({"message": "Chat added successfully", "id": chatId}), 201


@chat.route('/api/get_chats', methods=['POST'])
def get_chats():
    try:
        data = GetChat.parse_obj(request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    session = SessionLocal()
    
    try:
        chats = Chats.get_chats_by_username(data.username)

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"chats": [{
        "id": chat.id,
        "chat_name": chat.chat_name,
        "content": chat.content,
        "timestamp": chat.timestamp.isoformat()
    } for chat in chats
    ]}), 200

@chat.route('/api/delete_chat', methods=['POST'])
def delete_chat():
    try:
        data = GetChatInfo.parse_obj(request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    session = SessionLocal()
    
    try:
        chat = Chats.get_chat_by_id(session, data.id)
        session.delete(chat)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"message" : "Chat deleted"}), 200

@chat.route('/api/get_chat_info', methods=['POST'])
def get_chat_info():
    try:
        data = GetChatInfo.parse_obj(request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    session = SessionLocal()

    try:
        chat = Chats.get_chat_by_id(session, data.id)
        #print(chat.content)

        try:
            messages = json.loads(chat.content) if chat.content else []
        except json.JSONDecodeError:
            messages = []

        if chat:
            return jsonify({"messages": messages}), 200
        else:
            return jsonify({"error": "Chat not found"}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

@chat.route('/api/add_message', methods=['POST'])
def add_message():
    try:
        data = AddMsg.parse_obj(request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    

    session = SessionLocal()

    try:
        print(data)
        chat = Chats.get_chat_by_id(session, data.id)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404

        try:
            messages = json.loads(chat.content) if chat.content else []
        except json.JSONDecodeError:
            messages = []

        resp = client.moderations.create(
            model="omni-moderation-latest",
            input=data.content
        )
        r = resp.results[0]
        print(resp.model_dump_json(indent=2))
        if getattr(r, "flagged", True):            
            return jsonify({"response": "Message flagged as inappropriate"}), 200

        prompt = create_vectorstore(data.content, retriever)
        print(prompt)

        request_messages = []
        clean_messages = sanitize_history(messages, keep_placeholders=False)
        clean_messages.append({
            "role": "system",
            "content": prompt
        })

        request_messages.append({
            "role": "user",
            "content": prompt
        })
        messages.append({
            "role": "user",
            "content": data.content
        })

        
        print(clean_messages)

        #print(request_messages)

        chat.content = json.dumps(messages, ensure_ascii=False)
        session.commit()        

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=clean_messages,
            max_tokens=1000,
            temperature=0.7,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        print(json.dumps(message.model_dump(), indent=2))
        assistant_message = ""


        if message.content:
                assistant_message += response.choices[0].message.content   

        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name == "get_summary_by_title":
                assistant_message = arguments["title"] + '\n\n' + get_summary_by_title(**arguments) + '\n'
          
        
        
        base_assistant_message = assistant_message
        msg_text = f"{getattr(message, 'content', '') or ''}"

        if data.image and  BLOCK not in norm(msg_text):
            response = client.images.generate(
                model="dall-e-3",
                prompt=base_assistant_message,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="b64_json"
            )
            base64_image = response.data[0].b64_json
            assistant_message += f"\n[image]{base64_image}[/image]"

        if data.sound and  BLOCK not in norm(msg_text):
            audio_response = client.audio.speech.create(
                model="tts-1",
                voice="shimmer",
                input=base_assistant_message
            )
            audio_bytes = audio_response.read()
            base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            assistant_message += f"\n[audio]{base64_audio}[/audio]"

        messages.append({
            "role": "assistant",
            "content": assistant_message
        })

        #print(messages)

        chat.content = json.dumps(messages, ensure_ascii=False)
        session.commit()

        return jsonify({"response": assistant_message}), 201

    except Exception as e:
        session.rollback()
        print(f"Error adding message: {e}")
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

@chat.route('/api/audio_to_text', methods=['POST'])
def audio_to_text():
    try:
        body = request.get_json(force=True)
        b64 = body.get("audio", "")
        if b64.startswith("data:"):
            b64 = b64.split(",", 1)[1]

        audio_bytes = base64.b64decode(b64)
    except Exception as e:
        return jsonify({"error": f"Invalid audio payload: {e}"}), 400
    
    tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
    try:
        tmp.write(audio_bytes)
        tmp.flush()
        tmp.close()

        with open(tmp.name, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f,
            )

        text = getattr(transcript, "text", None) or transcript.get("text")
        return jsonify({"text": text}), 200

    finally:
        try: os.remove(tmp.name)
        except: pass



def get_summary_by_title(title):
    try:
        with open("book_summaries.txt", "r", encoding="utf-8") as file:
            summaries = file.readlines()
        for i in range(len(summaries)):
            if title in summaries[i].strip():
                return summaries[i + 1].strip() if i + 1 < len(summaries) else "No summary available."
        return "No summary found for that title."
    except FileNotFoundError:
        return "Summary file not found."
    
def strip_media_tags(text: str, keep_placeholder: bool = False) -> str:
    if not text:
        return ""
    def _repl(m):
        return f"[{m.group(1).lower()} omitted]" if keep_placeholder else ""
    cleaned = MEDIA_TAG_RE.sub(_repl, text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

def sanitize_history(messages, keep_placeholders: bool = False):
    cleaned = []
    for m in messages or []:
        role = m.get("role", "user")
        content = strip_media_tags(m.get("content", ""), keep_placeholders)
        if content: 
            cleaned.append({"role": role, "content": content})
    return cleaned

def norm(s: str) -> str:
    s = decode_unicode_escapes(s)
    s = (s or "").casefold().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = " ".join(s.split())      
    print(s)                      
    return s

def decode_unicode_escapes(s: str) -> str:
    if not s:
        return ""
    if _ue_re.search(s):          
        try:
            return codecs.decode(s, "unicode_escape")
        except Exception:
            pass
    return s