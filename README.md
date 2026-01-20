# 🚀 SkillProtocol - AI-Powered Skill Verification

> Turn Your GitHub Into Verified Credits Using NCrF & SFIA Standards

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)

**Built for "Commit To Change" AI Agents Hackathon 2026**

---

## 🎯 The Problem

**76% of employers want skills, not degrees** — but how do you prove your skills?

- ❌ Resumes are static PDFs
- ❌ Portfolios require manual updates
- ❌ Certifications are expensive
- ❌ GitHub activity is invisible to recruiters

**SkillProtocol solves this** by automatically analyzing your code and awarding verified, immutable skill credits based on industry standards.

---

## ✨ Features

- 🤖 **5 AI Agents** working together using LangGraph
- 📊 **NCrF Credits** - India's National Credit Framework standard
- 🏆 **SFIA Grading** - Global Skills Framework (Levels 1-5)
- ✅ **Reality Check** - Verifies code actually works via GitHub Actions
- 🔍 **Full Transparency** - Every decision traced in Opik
- 🔒 **Private Repos** - Supports both public and private repositories
- 🎨 **Beautiful UI** - Modern React with glassmorphism & animations
- 🎉 **Confetti Celebration** - When credits are awarded!

---

## 🏗️ Architecture

```
┌─────────────┐
│   React     │  Frontend (Vercel)
│   + Vite    │
└──────┬──────┘
       │ HTTPS
       ↓
┌─────────────┐
│   FastAPI   │  API Server (Render)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  LangGraph  │  Agent Orchestrator
│  5 Agents   │
└──────┬──────┘
       │
   ┌───┴────┬──────────┬──────────┐
   ↓        ↓          ↓          ↓
┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐
│GitHub│ │ Groq │ │  Opik  │ │  Neon  │
│ API  │ │ AI   │ │ Trace  │ │  DB    │
└──────┘ └──────┘ └────────┘ └────────┘
```

---

## 🚀 Quick Start (15 Minutes)

### Prerequisites

```bash
# Check versions
python --version  # 3.11+
node --version    # 18+
docker --version  # Any version
```

### 1. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/skillprotocol.git
cd skillprotocol

# Copy environment templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

### 2. Configure API Keys

Edit `backend/.env`:

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xyz.neon.tech/skillprotocol

# GitHub Token (required)
# Get from: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_your_github_token_here

# LLM API - Choose ONE:

# Option A: Groq (FREE, FAST) ⭐ RECOMMENDED
GROQ_API_KEY=gsk_your_groq_key_here
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-70b-versatile

# Option B: xAI Grok
XAI_API_KEY=xai_your_key_here
LLM_PROVIDER=xai
LLM_MODEL=grok-beta

# Option C: OpenAI (if you have it)
OPENAI_API_KEY=sk-your_openai_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o

# Opik Observability (required for hackathon)
# Get from: https://www.comet.com/signup
OPIK_API_KEY=your_opik_key_here
OPIK_WORKSPACE=skillprotocol
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy your scoring engine
cp /path/to/scoring_engine.py app/services/scoring/engine.py

# Run database migrations
python -c "from app.models.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install
```

### 5. Start Everything

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 6. Test

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

Try analyzing: `https://github.com/fastapi/fastapi`

---

## 🔑 API Keys Guide

### Required Keys

| Service | Purpose | Get From | Free? |
|---------|---------|----------|-------|
| **GitHub Token** | Clone repos, check CI/CD | [github.com/settings/tokens](https://github.com/settings/tokens) | ✅ Yes |
| **Groq API** | LLM for SFIA grading | [console.groq.com](https://console.groq.com) | ✅ Yes (fast!) |
| **Opik** | Observability & tracing | [comet.com/signup](https://www.comet.com/signup) | ✅ Yes |
| **Neon** | PostgreSQL database | [neon.tech](https://neon.tech) | ✅ Yes |

### Optional Keys

| Service | Purpose | Get From |
|---------|---------|----------|
| xAI Grok | Alternative LLM | [console.x.ai](https://console.x.ai) |
| OpenAI | Alternative LLM | [platform.openai.com](https://platform.openai.com) |

### GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scope: ✅ **repo** (Full control of private repositories)
4. Generate & copy token (starts with `ghp_`)

### Groq API Setup (Recommended)

1. Visit https://console.groq.com
2. Sign up (free!)
3. Create API key
4. Copy key (starts with `gsk_`)

**Why Groq?**
- ✅ Completely FREE
- ✅ Very FAST (up to 750 tokens/sec)
- ✅ Compatible with OpenAI SDK
- ✅ Llama 3.1 70B model

---

## 📁 Project Structure

```
skillprotocol/
├── frontend/              # React + Vite
│   ├── src/
│   │   ├── components/    # 4 pages
│   │   ├── App.jsx
│   │   └── index.css
│   └── package.json
├── backend/               # FastAPI + LangGraph
│   ├── app/
│   │   ├── agents/        # 6 AI agents
│   │   ├── api/           # REST endpoints
│   │   ├── core/          # Configuration
│   │   ├── services/      # Scoring engine
│   │   └── tools/         # GitHub, Opik
│   └── requirements.txt
├── docs/                  # Documentation
└── README.md              # This file
```

---

## 🤖 The 5 AI Agents

### 1. **Validator Agent**
- Checks if repo exists and is accessible
- Detects public vs private
- Gets repo metadata (size, language, stars)

### 2. **Scanner Agent**
- Clones repository (shallow clone)
- Runs NCrF calculation (SLOC, complexity, learning hours)
- Detects SFIA markers (tests, Docker, CI/CD)

### 3. **Grader Agent**
- Calls Groq API with SFIA rubric prompt
- Assigns skill level (1-5)
- Provides reasoning and evidence

### 4. **Auditor Agent**
- Checks if code actually works
- Queries GitHub Actions for test results
- Applies 50% penalty if tests fail

### 5. **Reporter Agent**
- Calculates final credits: `NCrF × SFIA × Reality Check`
- Saves to database
- Generates certificate

---

## 🧪 Testing

### Test Single Repo

```bash
cd backend
python test_analysis.py

# Choose option 1 or 2
```

### Test via API

```bash
# Start analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/fastapi/fastapi",
    "user_id": "test-user"
  }'

# Get job_id from response, then check status
curl http://localhost:8000/api/status/{job_id}

# Get final result
curl http://localhost:8000/api/result/{job_id}
```

### Run Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

---

## 🚀 Deployment

### Frontend (Vercel)

```bash
cd frontend
vercel --prod
```

### Backend (Render)

1. Create new "Web Service"
2. Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `.env`

### Database (Already on Neon)

Already configured in `.env`!

---

## 🔧 Configuration

### Using Groq (Default)

```bash
# backend/.env
GROQ_API_KEY=gsk_your_key
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-70b-versatile
```

### Using xAI Grok

```bash
# backend/.env
XAI_API_KEY=xai_your_key
LLM_PROVIDER=xai
LLM_MODEL=grok-beta
```

### Using OpenAI

```bash
# backend/.env
OPENAI_API_KEY=sk_your_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

---

## 📊 API Endpoints

### `POST /api/analyze`
Start repository analysis

**Request:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "user_id": "user-123",
  "github_token": "ghp_xxx (optional, for private repos)"
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "message": "Analysis started"
}
```

### `GET /api/status/{job_id}`
Check analysis progress

**Response:**
```json
{
  "job_id": "uuid",
  "status": "running",
  "current_step": "grader",
  "progress": 70,
  "errors": []
}
```

### `GET /api/result/{job_id}`
Get final credits

**Response:**
```json
{
  "job_id": "uuid",
  "final_credits": 12.5,
  "sfia_level": 4,
  "sfia_level_name": "Enable",
  "opik_trace_url": "https://...",
  "validation": {...},
  "scan_metrics": {...}
}
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### "Failed to connect to backend"

Make sure backend is running:
```bash
cd backend
uvicorn app.main:app --reload
```

### "Database connection error"

Check your `DATABASE_URL` in `.env`. For Neon:
```
postgresql+asyncpg://user:pass@ep-xyz.neon.tech/dbname
```

### "Groq API error"

Verify your API key:
```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

---

## 📚 Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** - Detailed setup guide
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - How everything connects
- **[Private Repos](docs/PRIVATE_REPO_GUIDE.md)** - Using private repositories
- **[API Documentation](docs/API.md)** - Complete API reference
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment

---

## 🎯 Hackathon Submission

### Prizes Targeting

- ✅ **Best Use of Opik** ($5,000) - Full tracing of all agents
- ✅ **Productivity & Work Habits** ($5,000) - Helps build verifiable portfolios

### Demo Video Script

1. **0:00-0:15** - Problem: "76% want skills, not degrees"
2. **0:15-0:30** - Solution: Paste GitHub URL
3. **0:30-1:00** - Live agent progress (all 5 agents)
4. **1:00-1:30** - Certificate with confetti 🎉
5. **1:30-2:00** - Opik trace (transparency!)

### Key Features to Highlight

- ✅ True multi-agent system (5 specialized agents)
- ✅ Industry standards (NCrF + SFIA)
- ✅ Full observability (Opik tracing)
- ✅ Real-world ready (private repos, error handling)
- ✅ Beautiful UX (animations, real-time updates)

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **Comet/Opik** - Observability platform
- **Groq** - Fast, free LLM inference
- **NCrF** - National Credit Framework
- **SFIA Foundation** - Skills framework
- **Hackathon Organizers** - For the opportunity!

---

## 📞 Contact

- **Team**: Your Name
- **Email**: your.email@example.com
- **Demo**: https://skillprotocol.vercel.app
- **GitHub**: https://github.com/yourusername/skillprotocol

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐!

---

**Built with ❤️ for the "Commit To Change" AI Agents Hackathon 2026**

**Turn Your GitHub Into Verified Credits! 🚀**