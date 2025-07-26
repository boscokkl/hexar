# Hexar - Agentic Web Gear Comparison Platform

> **Experimental AI-powered gear comparison platform where specialized agents collaborate to serve users**

Hexar demonstrates an innovative **multi-agent architecture** where AI agents work together to provide personalized snowboard gear recommendations. Each agent has specialized capabilities, from understanding user preferences to searching vendor catalogs.

## 🧠 Core Concept: Multi-Agent System

```
User Query → Consumer Agent → MCP → Vendor Agents → Personalized Results
```

- **Consumer Agent**: User's personal AI assistant (learns preferences, handles queries)
- **Vendor Agents**: Site-specific specialists (Evo.com, Burton.com, etc.)
- **MCP (Multi-Agent Communication Protocol)**: Standardized agent messaging

## 🏗️ Architecture

### Frontend (hexar-frontend/)
- **Framework**: Next.js 14 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand for agent communication
- **Real-time**: WebSocket connections for agent status
- **Auth**: Supabase

### Backend (hexar-backend/)
- **Language**: Python 3.9+ (AI/ML ecosystem)
- **Framework**: FastAPI (async API services)
- **AI Framework**: LangChain (agent orchestration, ReAct patterns)
- **LLM**: Google Gemini
- **Message Broker**: Redis (inter-agent communication)
- **Database**: PostgreSQL via Supabase

### Infrastructure
- **Orchestration**: Docker Compose
- **Monitoring**: Prometheus (optional)
- **Deployment**: Production-ready containers

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

### 1. Clone and Setup
```bash
git clone https://github.com/boscokkl/hexar.git
cd hexar

# Copy environment templates
cp .env.example .env
cp hexar-frontend/.env.local.example hexar-frontend/.env.local
```

### 2. Configure Environment
Edit `.env` with your credentials:
```bash
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Frontend Environment
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Start Full System
```bash
# Start all services with Docker Compose
docker-compose up -d

# Or for development with logs
docker-compose up
```

### 4. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Monitoring**: http://localhost:9090 (Prometheus)

## 🛠️ Development

### Frontend Development
```bash
cd hexar-frontend
npm install
npm run dev        # Start Next.js dev server
npm run build      # Build for production
npm run lint       # Run ESLint
```

### Backend Development
```bash
cd hexar-backend
pip install -r requirements.txt
python main.py     # Start FastAPI server

# Test agent communication
python -m agents.consumer_agent --user-id test123
```

### Agent Testing
```bash
# Test consumer agent
curl -X POST localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"search_query": "intermediate all-mountain snowboard under $500"}'

# Health check
curl localhost:8000/health
```

## 🤖 Agent System

### Consumer Agent (LangChain-based)
- **Purpose**: User's personal AI assistant
- **Capabilities**: Natural language processing, preference learning, query coordination
- **Memory**: Conversation buffer with context retention
- **Tools**: Vendor coordination, preference analysis, result processing

### Vendor Agents
- **Evo Agent**: Specialized for Evo.com product searches
- **Base Framework**: Extensible for additional vendors (Burton, REI, etc.)
- **Capabilities**: Product search, price comparison, availability checking
- **Fallback**: Graceful degradation when vendors are unavailable

### Message Broker (MCP)
- **Technology**: Redis-based message queue
- **Features**: Priority queues, agent registry, heartbeat monitoring
- **Patterns**: Pub/sub for broadcasts, direct messaging for coordination
- **Reliability**: Timeout handling, retry logic, dead letter queues

## 📁 Project Structure

```
hexar/
├── hexar-frontend/              # Next.js + TypeScript interface
│   ├── src/app/                # App Router (chat, onboarding, results)
│   ├── src/components/         # HexarChart, ResultsDisplay
│   ├── src/lib/agents/         # Frontend agent communication
│   └── src/lib/stores/         # Agent state management
├── hexar-backend/              # Python multi-agent system
│   ├── agents/                 # Agent implementations
│   │   ├── consumer_agent.py   # LangChain user agent
│   │   └── vendor_agents/      # Site-specific agents
│   ├── mcp/                    # Multi-Agent Communication Protocol
│   ├── models/                 # Pydantic schemas
│   └── services/               # Orchestrator, message broker
├── docker-compose.yml          # Full system deployment
└── monitoring/                 # Agent health tracking
```

## 🔧 Key Features

### Multi-Agent Coordination
- **Autonomous Agents**: Each agent operates independently with specialized skills
- **Fault Tolerance**: System continues functioning even if some agents fail
- **Scalability**: Agents can run on separate containers/servers
- **Extensibility**: Easy to add new vendor agents or capabilities

### Intelligent Product Comparison
- **Natural Language Queries**: "Find me an intermediate all-mountain board under $400"
- **Multi-Dimensional Analysis**: Price, quality, performance, style ratings
- **Personalized Results**: Learning user preferences over time
- **Real-time Data**: Live product information from multiple vendors

### Production-Ready Architecture
- **Docker Deployment**: Complete containerized setup
- **Health Monitoring**: Built-in health checks and metrics
- **Error Handling**: Comprehensive error recovery and logging
- **Security**: Environment-based configuration, no hardcoded secrets

## 🎯 Risk Mitigation

**Vendor Dependencies**: E-commerce sites frequently change structure
- **Multiple Data Sources**: APIs, product feeds, community sources
- **Fallback Hierarchy**: API → Scraping → Cached data → AI estimates
- **Graceful Degradation**: Partial results better than no results

## 🔮 Future Roadmap

- [ ] Additional vendor agents (Burton, REI, Backcountry)
- [ ] Advanced user preference learning
- [ ] Real-time price tracking and alerts
- [ ] Mobile app with agent communication
- [ ] Marketplace integration and affiliate partnerships
- [ ] Advanced analytics and user behavior insights

## 📄 Documentation

- **Architecture**: See [CLAUDE.md](./CLAUDE.md) for detailed technical specifications
- **API Docs**: Available at `/docs` when running the backend
- **Agent Specs**: Individual agent documentation in respective directories

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Issues**: [GitHub Issues](https://github.com/boscokkl/hexar/issues)
- **Discussions**: [GitHub Discussions](https://github.com/boscokkl/hexar/discussions)
- **Documentation**: [CLAUDE.md](./CLAUDE.md)

---

**Built with ❤️ for the future of AI-powered e-commerce**