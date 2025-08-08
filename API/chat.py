from flask import Blueprint, request, jsonify
from Database.chat_db import Chats, SessionLocal
from Database.user_db import User
from records.addchat import AddChat
from records.getchat import GetChat
from pydantic import ValidationError
from datetime import datetime, timezone
import os

chat = Blueprint('add_chat', __name__)
#openai.api_key = os.getenv("OPENAI_API_KEY") 

@chat.route('/api/add_chat', methods=['POST'])
def add_chat():
    try:
        data = AddChat.parse_obj(request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    session = SessionLocal()
    
    try:
        log = Chats(
            username=data.username,
            chat_name=data.chatname,
            content="",
            timestamp=datetime.utcnow()
        )

        session.add(log)
        session.commit()

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        session.close()

    return jsonify({"message": "Chat added successfully"}), 201


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