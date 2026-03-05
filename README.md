# AI Smart Local Commerce Communication Platform

An **AI-powered communication layer for commerce platforms** that automatically reaches out to customers when important order events occur (e.g., delivery failure, order confirmation).

The system seamlessly orchestrates AI voice calls, dynamic customer speech recognition, and intelligent fallbacks (like WhatsApp messages) if a call fails or is unanswered. It supports a **provider-based architecture** that gracefully switches between high-quality production APIs (when keys are provided) and open-source/local simulated backends (for free local development).

---

## 🚀 Features

- **Order Event Integration**: Processes webhooks from Shopify, WooCommerce, and other commerce platforms.
- **Provider-Based Architecture**: Automatically falls back to free open-source simulators if production API keys aren't provided.
  - **Voice Providers**: Twilio API vs. Local Simulated Call Simulator
  - **Speech/TTS Providers**: ElevenLabs, OpenAI Whisper vs. offline tools (pyttsx3, Piper TTS)
  - **Messaging Providers**: Meta WhatsApp API vs. Local Simulated Messaging Pipeline
- **AI Voice Calling**: Initiates phone calls with dynamically generated TTS and captures speech responses to determine user intent (e.g., reschedule, cancel).
- **Intelligent Fallback**: Sends a WhatsApp confirmation message if the voice call fails.
- **Microservices Architecture**: Built with FastAPI, PostgreSQL, and Redis (task queues) for performance and horizontal scalability over Docker.
- **Vendor Dashboard**: A frontend interface to monitor logs, calls, and order status events.

---

## 🛠️ Technology Stack

- **Backend System**: Python, FastAPI
- **Database Engine**: PostgreSQL
- **Task Queue Engine**: Redis
- **Frontend Layer**: Vanilla HTML, CSS, JavaScript
- **Infrastructure**: Docker & Docker Compose

---

## 📋 System Workflow

**1. Primary Flow (AI Voice Call)**
`Order Event` ➔ `AI Voice Call` ➔ `Dynamic Customer Response` ➔ `Intent Parsed` ➔ `Order Status Updated`

**2. Fallback Flow (WhatsApp)**
`Order Event` ➔ `AI Voice Call` ➔ *Call Failed / Voicemail* ➔ `Send WhatsApp Message`

---

## 🔧 Installation & Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local, non-Docker execution)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/AI-Commerce.git
cd AI-Commerce
```

### 2. Environment Configuration
Copy the example environment variables file and update your keys (if using production APIs). 
If you leave the keys empty, the system will use the **free, local simulators**.

```bash
cp example.env .env
```

### 3. Quick Start (Docker - Recommended)
The fastest way to start is using Docker. It builds the API, Postgres, and Redis:

```bash
docker-compose up -d --build
```
> The API will be available at `http://localhost:8000`. The frontend starts within the same server ecosystem or can be served using Live Server.

### 4. Local Development Without Docker
To run locally directly on your desktop:

**Start Postgres & Redis**:
Have local instances of Postgres and Redis running, and update your `.env` to point to localhost.

**Start the Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the FastAPI Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 Project Structure

```text
├── .env                # Secret keys (ignored by git - use example.env)
├── docker-compose.yml  # Microservices orchestrator
├── backend/            # FastAPI Backend Application
│   ├── main.py         # Entry point for the FastAPI server
│   ├── database.py     # SQLAlchemy DB connection setup
│   ├── models.py       # ORM Database Models
│   ├── queue_manager.py # Celery/Redis Job scheduling
│   ├── routers/        # API route handlers
│   ├── services/       # Core business logic
│   └── providers/      # Architecture abstractions (Voice, TTS, Messaging)
└── frontend/           # HTML/JS/CSS UI Dashboard
    ├── index.html      # Main dashboard page
    ├── communications.html
    └── simulate.html   # Sandbox for testing the pipelines locally
```

---

## 🌐 Endpoints overview
You can interact with the Swagger documentation to see all endpoints and schemas available. After starting the server, navigate to:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Ref**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 💡 Developer Guidelines
- **Adding new Providers**: Extend the base provider classes found in `backend/providers/base.py`. Implementing a new SMS or TTS gateway requires satisfying the base abstract properties.
- **Handling Webhooks**: Register new commerce provider payload structures in `backend/routers/webhooks.py`.
