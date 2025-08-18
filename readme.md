# Book Retrieval GPT

Book Retrieval GPT is a conversational web application that uses OpenAI's GPT-4o and RAG (Retrieval-Augmented Generation) techniques to answer questions about books, generate summaries, and provide audio/image responses. It features persistent chat history, user authentication, and real-time speech-to-text.

## Technologies Used

- **Python 3.11**
- **Flask**: Web framework for API and routing
- **Flask-Sock**: WebSocket support for real-time speech-to-text
- **SQLAlchemy**: ORM for PostgreSQL database
- **PostgreSQL**: Persistent storage for chats and users
- **OpenAI API**: GPT-4o for chat, DALL-E for images, TTS for audio, and Realtime for speech-to-text
- **LangChain**: RAG pipeline for book context retrieval
- **ChromaDB**: Vector database for semantic search
- **Pydantic**: Data validation for API requests
- **Docker & Docker Compose**: Containerization and orchestration
- **Gunicorn + Eventlet**: Production WSGI server with async support
- **HTML/CSS/JS**: Frontend interface with real-time chat, audio, and image rendering

## Features

- **RAG (Retrieval-Augmented Generation)**: Uses semantic search to find relevant book chunks
<img src="imgs/llm3.png" alt="" width="300px"/>
- **Conversational Q&A** about books using GPT-4o and context from book summaries
- **Audio & Image Generation**: Optionally returns TTS audio and DALL-E images for responses
- **Speech-to-Text**: Real-time transcription using OpenAI Realtime API
- **User Authentication**: Simple username-based login
- **Persistent Chat History**: Chats and messages stored in PostgreSQL
- **Responsive UI**: Modern, mobile-friendly design

## Project Structure

```
├── api/
│   └── chat.py           # Flask Blueprint for chat API
├── app/
│   └── rag.py            # RAG pipeline and vectorstore setup
├── Database/
│   ├── chat_db.py        # SQLAlchemy models for chats
│   └── user_db.py        # SQLAlchemy models for users
├── records/              # Pydantic models for API requests
├── static/
│   └── pcm16-writer.js   # AudioWorklet for PCM16 streaming
├── templates/
│   ├── auth.html         # Login page
│   └── page.html         # Main chat UI
├── book_summaries.txt    # Book summaries used for RAG
├── Dockerfile            # Container build instructions
├── docker-compose.yaml   # Multi-service orchestration
├── requirements.txt      # Python dependencies
├── start.sh, wait-for-it.sh # Entrypoint scripts
├── main.py               # App entrypoint and WebSocket handler
└── __init__.py           # Flask app factory
```

## Setup & Build Instructions

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- OpenAI API Key (for GPT, DALL-E, TTS, Realtime)

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/book-retrieval-gpt.git
cd book-retrieval-gpt
```

### 2. Set Environment Variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...your-key...
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
PORT=5000
```

### 3. Build and Start with Docker Compose

```sh
docker-compose up --build
```

- The app will be available at [http://localhost:8000](http://localhost:8000)
- PostgreSQL runs on port `25432` (internal: `5432`)

### 4. Manual Local Development (Optional)

If you want to run locally without Docker:

1. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
2. Start PostgreSQL and set `DATABASE_URL` accordingly.
3. Run the app:
    ```sh
    export OPENAI_API_KEY=sk-...your-key...
    export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
    python main.py
    ```
4. Visit [http://localhost:5000](http://localhost:5000)

## Usage

1. **Login**: Enter a username to start a session.
2. **Create/Select Chat**: Start a new chat or select an existing one.
3. **Ask Questions**: Type questions about books. Optionally enable "Return Audio" or "Return Picture" for TTS/image responses.
4. **Speech-to-Text**: Click the microphone to dictate your question.
5. **View Responses**: Answers may include text, images, or audio players.

## API Endpoints

- `/api/add_chat` - Create a new chat
- `/api/get_chats` - List chats for user
- `/api/delete_chat` - Delete a chat
- `/api/get_chat_info` - Get messages for a chat
- `/api/add_message` - Add a message and get GPT response
- `/api/audio_to_text` - Transcribe audio to text

## Customization

- **Book Summaries**: Add or edit summaries in [`book_summaries.txt`](book_summaries.txt)
- **RAG Pipeline**: Modify retrieval logic in [`app/rag.py`](app/rag.py)
- **Frontend**: Update UI in [`templates/page.html`](templates/page.html)

## Troubleshooting

- Ensure your OpenAI API key is valid and has access to GPT-4o, DALL-E, TTS, and Realtime endpoints.
- If using Docker, the app waits for the database to be ready before starting.
- For vectorstore issues, ensure `chroma_books/` is writable and persists between runs.

## License

MIT License

---

**Book Retrieval GPT** © 2024. Powered by OpenAI, Flask, LangChain, and ChromaDB.