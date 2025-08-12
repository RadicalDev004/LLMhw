from flask import Blueprint, request, jsonify
from Database.chat_db import Chats, SessionLocal
from Database.user_db import User
from records.addchat import AddChat
from records.getchat import GetChat
from records.addmessage import AddMsg
from records.getchatinfo import GetChatInfo
from pydantic import ValidationError
import json
from datetime import datetime, timezone
import traceback
import os
from openai import OpenAI
from app.rag import create_vectorstore, retriever, initialize_vectorstore

chat = Blueprint('add_chat', __name__)

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
#openai.api_key = os.getenv("OPENAI_API_KEY", "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") 

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
        #print(data.id)
        print(chat)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404

        try:
            messages = json.loads(chat.content) if chat.content else []
        except json.JSONDecodeError:
            messages = []

        prompt = create_vectorstore(data.content, retriever)
        print(prompt)
        request_messages = []
        request_messages.append({
            "role": "user",
            "content": prompt
        })
        messages.append({
            "role": "user",
            "content": data.content
        })

        #print(request_messages)

        chat.content = json.dumps(messages, ensure_ascii=False)
        session.commit()
        client = OpenAI(api_key="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")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=request_messages,
            max_tokens=1000,
            temperature=0.7,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        assistant_message = ""

        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name == "get_summary_by_title":
                assistant_message = arguments["title"] + '\n' + get_summary_by_title(**arguments)
        elif message.content:
            assistant_message = response.choices[0].message.content  

        else:
            raise Exception("No content in the response message.")  

        if data.image and  "Nu am suficiente informatii pentru a raspunde la aceasta intrebare." not in data.content:
            response = client.images.generate(
                model="dall-e-3",
                prompt=assistant_message,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="b64_json"
            )
            base64_image = response.data[0].b64_json
            assistant_message += f"\n[image]{base64_image}[/image]"

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