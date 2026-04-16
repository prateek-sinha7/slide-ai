# 🎨 AI PowerPoint Generator

> **Generate professional PowerPoint presentations in minutes using AI - completely free and private!**

A full-stack web application powered by a multi-agent LangChain system with local Mistral LLM that creates stunning presentations from simple text prompts.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

---

## ✨ Features

### 🤖 AI-Powered Generation
- **Multi-Agent System**: 4 specialized AI agents (Planner, Writer, Editor, Designer)
- **Local LLM**: Uses Mistral 7B via Ollama - no API costs, complete privacy
- **Smart Content**: Structured outlines, detailed bullet points, and professional flow
- **Quality Assurance**: Multi-stage review process ensures high-quality output

### 🎯 Customization
- **Flexible Topics**: Generate presentations on any subject
- **Tone Control**: Choose from Formal, Casual, Fun, or Professional
- **Slide Count**: 5-20 slides based on your needs
- **Professional Templates**: Clean, modern slide designs

### 🔒 Security & Privacy
- **JWT Authentication**: Secure user accounts
- **Password Hashing**: bcrypt encryption
- **100% Local**: All data stays on your machine
- **No Cloud Dependencies**: Works completely offline

### 💎 User Experience
- **Modern UI**: Beautiful gradient design with glass-morphism effects
- **Real-time Progress**: Live updates with stage indicators
- **Fast Generation**: 2-3 minutes for complete presentations
- **Automatic Download**: Presentations download directly to your computer

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Next.js   │ ───> │   FastAPI   │ ───> │ Orchestrator│ ───> │   Ollama    │
│   Frontend  │ <─── │   Backend   │ <─── │  (4 Agents) │ <─── │  (Mistral)  │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                              │
                              ↓
                     ┌─────────────────┐
                     │  PPT Generator  │
                     │  (python-pptx)  │
                     └─────────────────┘
```

### Multi-Agent Pipeline

1. **Planner Agent** (30s) - Creates logical outline with slide titles
2. **Content Agent** (40s) - Generates 3-6 bullet points per slide
3. **Reviewer Agent** (40s) - Refines content and ensures quality
4. **Design Agent** (90s) - Assigns layouts and speaker notes

**Total Time**: 2-3 minutes for a complete presentation

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Ollama** - [Download](https://ollama.ai/)

### Automated Setup (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd SlideGenAI

# 2. Install and start Ollama
ollama serve

# 3. Pull Mistral model (in another terminal)
ollama pull mistral:latest

# 4. Run the setup script
./setup.sh
```

The script will:
- ✅ Check all prerequisites
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Start backend on http://localhost:8000
- ✅ Start frontend on http://localhost:3000

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

#### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run backend
python main.py
```

#### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings

# Run frontend
npm run dev
```

#### Start Ollama

```bash
# In a separate terminal
ollama serve

# Pull Mistral model
ollama pull mistral:latest
```

</details>

### Stop Servers

```bash
./stop.sh
```

---

## 📖 Usage

### 1. Open the Application
Navigate to **http://localhost:3000** in your browser

### 2. Create an Account
- Click "Register"
- Enter username and password
- You'll be automatically logged in

### 3. Generate a Presentation
- **Topic**: Enter your presentation topic (e.g., "Artificial Intelligence")
- **Tone**: Choose Professional, Formal, Casual, or Fun
- **Slides**: Select 5-20 slides (default: 8)
- Click **"Generate Presentation"**

### 4. Watch the Progress
The system will show real-time progress through 5 stages:
- 📋 Planning (creating outline)
- ✍️ Content (generating bullets)
- 🔍 Review (refining content)
- 🎨 Design (assigning layouts)
- 📦 Export (creating file)

### 5. Download Your Presentation
The .pptx file will automatically download to your Downloads folder!

---

## 📁 Project Structure

```
SlideGenAI/
├── frontend/                    # Next.js Frontend
│   ├── app/
│   │   ├── layout.tsx          # Root layout with AuthProvider
│   │   ├── page.tsx            # Main generator page
│   │   ├── auth/page.tsx       # Login/Registration
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── PromptForm.tsx      # Input form with visual controls
│   │   ├── ProgressIndicator.tsx  # Real-time progress display
│   │   ├── ErrorDisplay.tsx    # Error handling UI
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
│   ├── auth/                   # Authentication Module
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
│   ├── orchestrator/           # LLM Multi-Agent System ⭐
│   │   ├── orchestrator.py     # Main coordinator
│   │   ├── planner_agent.py    # Outline generation
│   │   ├── content_agent.py    # Content generation
│   │   ├── reviewer_agent.py   # Content refinement
│   │   ├── design_agent.py     # Layout assignment
│   │   ├── models.py           # Pydantic models
│   │   ├── config.py           # Orchestrator config
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── ppt_generator/          # PowerPoint Generation
│   │   ├── generator.py        # PPT creation logic
│   │   └── timeout.py          # Timeout utilities
│   │
│   ├── tests/                  # Test Suite
│   │   ├── test_auth_*.py      # Auth tests
│   │   ├── test_ppt_*.py       # PPT tests
│   │   └── test_integration_*.py  # Integration tests
│   │
│   ├── temp_presentations/     # Temporary storage
│   ├── users.db                # SQLite database
│   └── requirements.txt        # Dependencies
│
├── .kiro/                      # Kiro AI Specs
│   └── specs/ai-ppt-generator/
│       ├── requirements.md     # Feature requirements
│       ├── design.md           # Technical design
│       └── tasks.md            # Implementation tasks
│
├── setup.sh                    # Automated setup script
├── stop.sh                     # Stop servers script
├── START_HERE.md               # Quick start guide
├── DEMO_PRESENTATION_GUIDE.md  # Demo documentation
├── ARCHITECTURE_DIAGRAMS.md    # Technical diagrams
├── SIMPLE_ARCHITECTURE_DIAGRAM.md  # Non-technical diagrams
└── README.md                   # This file
```

---

## 💻 Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework with server-side rendering |
| **TypeScript** | Type safety and better developer experience |
| **React 18** | UI component library |
| **Axios** | HTTP client for API calls |
| **CSS-in-JS** | Scoped styling with CSS variables |
| **JWT** | Token-based authentication |

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance Python web framework |
| **LangChain** | LLM application framework |
| **Ollama** | Local LLM runtime |
| **Mistral 7B** | Open-source language model |
| **Pydantic v2** | Data validation and settings |
| **python-pptx** | PowerPoint file generation |
| **bcrypt** | Password hashing |
| **PyJWT** | JWT token management |
| **SQLite** | User database |
| **pytest** | Testing framework |

### AI/LLM
| Component | Description |
|-----------|-------------|
| **Ollama** | Runs Mistral locally on port 11434 |
| **Mistral 7B** | 7 billion parameter model (4.4 GB) |
| **LangChain** | Orchestrates multi-agent pipeline |
| **4 Agents** | Planner, Content, Reviewer, Designer |

---

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

```bash
# LLM Provider (ollama, openai, anthropic)
LLM_PROVIDER=ollama
LLM_MODEL=mistral:latest
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Timeouts (seconds) - Adjusted for local model
PLANNER_TIMEOUT=90
CONTENT_TIMEOUT=120
REVIEWER_TIMEOUT=120
DESIGN_TIMEOUT=90
PIPELINE_TIMEOUT=420

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# File Configuration
TEMP_FILE_DIR=temp_presentations
FILE_EXPIRATION_HOURS=1
DEFAULT_SLIDE_COUNT=8
```

### Frontend Configuration (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest

# Run specific test file
pytest tests/test_auth_service.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- PromptForm.test.tsx
```

### Integration Tests

```bash
cd backend
pytest tests/test_integration_e2e.py -v
```

---

## 📊 Performance

### Generation Times (Mistral 7B Local)
- **5 slides**: ~2-3 minutes
- **8 slides**: ~3-4 minutes
- **20 slides**: ~5-7 minutes

### Agent Breakdown
- **Planner**: 20-30 seconds
- **Content**: 25-35 seconds
- **Reviewer**: 30-40 seconds
- **Design**: 50-90 seconds
- **PPT Generation**: <1 second

### Resource Usage
- **RAM**: 2-3 GB (Ollama + Mistral)
- **CPU**: Moderate during generation
- **Disk**: 4.4 GB (Mistral model)
- **Network**: None (fully local)

---

## 🐛 Troubleshooting

### Python 3.14+ Compatibility Issues

**Error:** `TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument`

**Solution:** Python 3.14 is too new. Use Python 3.9-3.13:
```bash
brew install python@3.13
cd backend
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Missing Rust Compiler

**Error:** `error: can't find Rust compiler`

**Solution:** Install Rust:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Pull Mistral model if needed
ollama pull mistral:latest
```

### Port Already in Use

```bash
# Kill process on port 8000 (backend)
lsof -ti :8000 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti :3000 | xargs kill -9

# Or use the stop script
./stop.sh
```

### Backend Fails to Start

```bash
# Check logs
cat logs/backend.log

# Common issues:
# 1. Missing .env file → Copy from .env.example
# 2. Dependencies not installed → pip install -r requirements.txt
# 3. Ollama not running → ollama serve
# 4. Wrong Python version → Use Python 3.9-3.13
```

### Frontend Fails to Start

```bash
# Check logs
cat logs/frontend.log

# Common issues:
# 1. Missing .env.local → Copy from .env.example
# 2. Dependencies not installed → npm install
# 3. Port 3000 in use → Kill process or change port
```

### Generation Timeout

If generation times out:
1. Increase timeouts in `backend/.env`
2. Reduce slide count
3. Use a faster model (if available)
4. Check system resources

**For more detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## 📚 Documentation

- **[START_HERE.md](START_HERE.md)** - Quick start guide
- **[DEMO_PRESENTATION_GUIDE.md](DEMO_PRESENTATION_GUIDE.md)** - Complete demo guide with technical details
- **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** - Technical architecture diagrams
- **[SIMPLE_ARCHITECTURE_DIAGRAM.md](SIMPLE_ARCHITECTURE_DIAGRAM.md)** - Non-technical diagrams for everyone
- **[QUICK_DEMO_REFERENCE.md](QUICK_DEMO_REFERENCE.md)** - Quick reference for demos

---

## 🎯 Use Cases

- **Business Presentations**: Sales pitches, quarterly reviews, project updates
- **Educational Content**: Lectures, training materials, workshops
- **Conference Talks**: Technical presentations, keynotes
- **Marketing**: Product launches, campaign overviews
- **Research**: Academic presentations, thesis defenses
- **Personal**: Event planning, hobby presentations

---

## 🚀 Future Enhancements

- [ ] **Image Generation**: AI-generated images for slides
- [ ] **Custom Themes**: User-uploadable PowerPoint templates
- [ ] **Presentation History**: Save and manage past presentations
- [ ] **Collaboration**: Share and edit presentations
- [ ] **Export Formats**: PDF, Google Slides, Keynote
- [ ] **Voice Narration**: AI-generated speaker audio
- [ ] **Real-time Editing**: Edit content before download
- [ ] **Analytics**: Track presentation effectiveness
- [ ] **Multi-language**: Support for multiple languages
- [ ] **Cloud Sync**: Optional cloud backup

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain** - For the amazing LLM framework
- **Ollama** - For making local LLMs accessible
- **Mistral AI** - For the excellent open-source model
- **FastAPI** - For the high-performance web framework
- **Next.js** - For the modern React framework
- **python-pptx** - For PowerPoint generation capabilities

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation in the `/docs` folder
- Review the troubleshooting section above

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ using AI and modern web technologies**

**Generate presentations in minutes, not hours! 🚀**
# slide-ai
