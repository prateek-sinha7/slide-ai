# 🎨 AI PowerPoint Generator

> **Generate professional PowerPoint presentations in minutes using AI-powered multi-agent system**

A full-stack web application that uses LangChain ReAct agents to create stunning presentations from simple text prompts. Supports multiple LLM providers including Groq, Anthropic Claude, OpenAI, and local Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9-3.13](https://img.shields.io/badge/python-3.9--3.13-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

---

## ✨ Features

### 🤖 AI-Powered Generation
- **4 ReAct Agents**: Autonomous agents with reasoning loops (Planner, Content, Reviewer, Designer)
- **Multi-LLM Support**: Groq, Anthropic Claude, OpenAI, Ollama
- **Smart Tools**: 10+ specialized tools for quality validation and optimization
- **Iterative Refinement**: Agents iterate 1-5 times until quality thresholds are met
- **Memory System**: Conversation memory and cross-agent result caching

### 🎯 Customization
- **Flexible Topics**: Generate presentations on any subject
- **Tone Control**: Professional, Formal, Casual, or Fun
- **Slide Count**: 5-20 slides
- **Professional Design**: Clean, modern slide layouts

### 🔒 Security
- **JWT Authentication**: Secure user accounts
- **Password Hashing**: bcrypt encryption
- **SQLite Database**: Local user management

### 💎 User Experience
- **Modern UI**: Beautiful gradient design with glass-morphism
- **Real-time Progress**: Live updates through 5 generation stages
- **Fast Generation**: 1-3 minutes for complete presentations
- **Automatic Download**: Direct .pptx file download

---

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Next.js   │ ───> │   FastAPI   │ ───> │ Orchestrator │ ───> │ LLM Provider│
│   Frontend  │ <─── │   Backend   │ <─── │  (4 Agents)  │ <─── │ (Multi-LLM) │
└─────────────┘      └─────────────┘      └──────────────┘      └─────────────┘
                              │
                              ↓
                     ┌─────────────────┐
                     │  PPT Generator  │
                     │  (python-pptx)  │
                     └─────────────────┘
```

### Multi-Agent Pipeline

1. **Planner Agent** - Creates logical outline with slide titles
2. **Content Agent** - Generates 3-6 bullet points per slide
3. **Reviewer Agent** - Refines content and ensures quality
4. **Design Agent** - Assigns layouts and speaker notes

**Total Time**: 1-3 minutes (cloud APIs) or 3-5 minutes (local Ollama)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9-3.13** ([Download](https://www.python.org/downloads/)) ⚠️ Python 3.14+ not supported
- **Node.js 16+** ([Download](https://nodejs.org/))
- **LLM Provider** (choose one):
  - **Groq API** (Recommended) - [Get API Key](https://console.groq.com)
  - **Anthropic Claude** - [Get API Key](https://console.anthropic.com)
  - **OpenAI** - [Get API Key](https://platform.openai.com)
  - **Ollama** (Local) - [Download](https://ollama.ai/)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd SlideGenAI

# 2. Run setup script
./setup.sh

# 3. Configure LLM provider
cd backend
nano .env  # Add your API key and configure provider
```

### Configuration

Edit `backend/.env`:

```bash
# Choose your LLM provider
LLM_PROVIDER=anthropic  # Options: groq, anthropic, openai, ollama

# Add your API key (for cloud providers)
GROQ_API_KEY=your-groq-api-key-here
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key-here
# OR
OPENAI_API_KEY=your-openai-api-key-here

# For Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=mistral:latest

# Agent settings
MAX_ITERATIONS=3
QUALITY_THRESHOLD=0.75

# LangSmith (Optional - for tracing and monitoring)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key-here
LANGSMITH_PROJECT=slide-ai
```

**📊 LangSmith Integration** (Optional but Recommended)

Enable comprehensive tracing and monitoring:

1. Sign up at [https://smith.langchain.com](https://smith.langchain.com)
2. Get your API key
3. Set `LANGSMITH_TRACING=true` in `.env`
4. View traces at https://smith.langchain.com

See [LangSmith Integration Guide](documents/LANGSMITH_INTEGRATION.md) for details.
```

### Start the Application

```bash
# Backend will start on http://localhost:8000
# Frontend will start on http://localhost:3000

# To stop servers
./stop.sh
```

---

## 📁 Project Structure

```
SlideGenAI/
├── frontend/                    # Next.js Frontend
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Main generator page
│   │   ├── auth/page.tsx       # Login/Registration
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── PromptForm.tsx      # Input form
│   │   ├── ProgressIndicator.tsx  # Progress display
│   │   ├── ErrorDisplay.tsx    # Error handling
│   │   ├── LoginForm.tsx       # Login component
│   │   └── RegistrationForm.tsx  # Registration component
│   ├── contexts/
│   │   └── AuthContext.tsx     # Authentication state
│   ├── services/
│   │   └── presentationService.ts  # API client
│   └── package.json
│
├── backend/                     # FastAPI Backend
│   ├── main.py                 # FastAPI app & endpoints
│   ├── config.py               # Configuration
│   │
│   ├── auth/                   # Authentication
│   │   ├── service.py          # User registration/login
│   │   ├── jwt.py              # JWT token management
│   │   ├── password.py         # Password hashing
│   │   ├── models.py           # User models
│   │   └── database.py         # SQLite operations
│   │
│   ├── api/                    # API Layer
│   │   ├── middleware.py       # JWT authentication
│   │   ├── validation.py       # Request validation
│   │   ├── error_handlers.py  # Error handling
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── orchestrator/           # LLM Multi-Agent System
│   │   ├── orchestrator.py     # Main coordinator
│   │   ├── planner_agent.py    # Outline generation
│   │   ├── content_agent.py    # Content generation
│   │   ├── reviewer_agent.py   # Content refinement
│   │   ├── design_agent.py     # Layout assignment
│   │   ├── memory.py           # Memory system
│   │   ├── models.py           # Pydantic models
│   │   ├── config.py           # Orchestrator config
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── tools/              # Agent Tools
│   │       ├── base_tool.py
│   │       ├── planner_tools.py
│   │       ├── content_tools.py
│   │       ├── reviewer_tools.py
│   │       ├── design_tools.py
│   │       └── tool_registry.py
│   │
│   ├── ppt_generator/          # PowerPoint Generation
│   │   ├── generator.py        # PPT creation logic
│   │   └── timeout.py          # Timeout utilities
│   │
│   ├── tests/                  # Test Suite
│   │   ├── test_auth_*.py      # Auth tests
│   │   ├── test_ppt_*.py       # PPT tests
│   │   ├── test_*_agent.py     # Agent tests
│   │   └── test_e2e_*.py       # Integration tests
│   │
│   ├── temp_presentations/     # Temporary storage
│   ├── users.db                # SQLite database
│   └── requirements.txt        # Dependencies
│
├── .kiro/                      # Kiro AI Specs
│   └── specs/
│       ├── ai-ppt-generator/   # Original spec
│       └── langchain-deep-agents/  # ReAct agents spec
│
├── logs/                       # Application logs
│   ├── backend.log
│   └── frontend.log
│
├── setup.sh                    # Automated setup script
├── stop.sh                     # Stop servers script
└── README.md                   # This file
```

---

## 💻 Technology Stack

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **React 18** - UI library
- **Axios** - HTTP client
- **JWT** - Authentication

### Backend
- **FastAPI** - Python web framework
- **LangChain** - LLM agent framework
- **Pydantic v2** - Data validation
- **python-pptx** - PowerPoint generation
- **bcrypt** - Password hashing
- **PyJWT** - JWT tokens
- **SQLite** - User database
- **pytest** - Testing

### AI/LLM
- **LangChain ReAct Agents** - 4 autonomous agents
- **Multi-Provider Support** - Groq, Anthropic, OpenAI, Ollama
- **10+ Specialized Tools** - Quality validation, grammar checking, layout optimization
- **Memory System** - Conversation memory + result caching

---

## ⚙️ LLM Provider Setup

### Option 1: Groq (Recommended - Fast & Affordable)

1. Get API key from [console.groq.com](https://console.groq.com)
2. Update `backend/.env`:
```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

**Available Models:**
- `llama-3.3-70b-versatile` (Recommended)
- `mixtral-8x7b-32768`
- `llama-3.1-8b-instant` (Fastest)

### Option 2: Anthropic Claude (High Quality)

1. Get API key from [console.anthropic.com](https://console.anthropic.com)
2. Update `backend/.env`:
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your_key_here
LLM_MODEL=claude-sonnet-4-20250514
```

**Cost:** ~$0.19 per presentation

### Option 3: OpenAI

1. Get API key from [platform.openai.com](https://platform.openai.com)
2. Update `backend/.env`:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_key_here
LLM_MODEL=gpt-4
```

### Option 4: Ollama (Local - Free & Private)

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Start Ollama: `ollama serve`
3. Pull model: `ollama pull mistral:latest`
4. Update `backend/.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=mistral:latest
```

---

## 🎯 Usage

1. **Open** http://localhost:3000
2. **Register** a new account
3. **Enter** your presentation topic
4. **Choose** tone and slide count
5. **Generate** and download your .pptx file!

---

## 📊 Performance

| Provider | 8 Slides | Quality | Cost |
|----------|----------|---------|------|
| **Groq** | ~60-90s | ⭐⭐⭐⭐ | Free (with limits) |
| **Anthropic** | ~90-120s | ⭐⭐⭐⭐⭐ | ~$0.19 |
| **OpenAI** | ~90-120s | ⭐⭐⭐⭐⭐ | ~$0.30 |
| **Ollama** | ~3-4min | ⭐⭐⭐ | Free |

---

## 🧪 Testing

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest

# Frontend tests
cd frontend
npm test
```

---

## 🐛 Troubleshooting

### Python 3.14+ Not Supported
```bash
# Use Python 3.9-3.13
brew install python@3.13  # macOS
cd backend
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Port Already in Use
```bash
./stop.sh
# Or manually:
lsof -ti :8000 | xargs kill -9  # Backend
lsof -ti :3000 | xargs kill -9  # Frontend
```

### LLM Provider Errors
- **Groq Rate Limit**: Wait for reset or switch models
- **Invalid API Key**: Check key format and validity
- **Ollama Not Running**: Run `ollama serve`

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **LangChain** - LLM agent framework
- **Groq** - Fast cloud inference
- **Anthropic** - Claude AI
- **OpenAI** - GPT models
- **Ollama** - Local LLM runtime
- **FastAPI** - Web framework
- **Next.js** - React framework
- **python-pptx** - PowerPoint generation

---

**Built with ❤️ using AI and modern web technologies**
