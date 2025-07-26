# Hexar - Agentic Web Gear Comparison Platform

## 🧠 Core Concept: Multi-Agent Architecture

Experimental platform where specialized AI agents collaborate to serve users:
- **Consumer Agent**: User's personal AI assistant (learns preferences, handles queries)
- **Vendor Agents**: Site-specific specialists (Evo.com, Burton.com, etc.)
- **MCP (Multi-Agent Communication Protocol)**: Standardized agent messaging

```
User Query → Consumer Agent → MCP → Vendor Agents → Personalized Results
```

# Tech Stack

**Frontend**
- Framework: **Next.js 14** + TypeScript
- Styling: Tailwind CSS + shadcn/ui
- State: Jotai/Zustand for agent communication
- Real-time: WebSocket connections
- Auth: Supabase

**Backend (Multi-Agent System)**
- Language: **Python 3.9+** (AI/ML ecosystem)
- Framework: **FastAPI** (async API services)
- AI Framework: **LangChain** (agent orchestration, ReAct patterns)
- LLM: **Google Gemini** or OpenAI GPT-4
- Message Broker: **RabbitMQ** (inter-agent communication)
- Database: **PostgreSQL** via Supabase

**Key Dependencies**
```python
# Backend core
fastapi>=0.116.1
langchain>=0.1.0
google-generativeai>=0.3.2
celery[redis]>=5.3.0  # For RabbitMQ
supabase>=2.0.0

# Agent tools
beautifulsoup4>=4.12.2
selenium>=4.15.0
requests>=2.31.0
```

# Project Structure

```
hexar/
├── hexar-frontend/              # Next.js + TypeScript interface
│   ├── src/app/                # App Router (chat, onboarding, results)
│   ├── src/components/         # AgentStatusFeed, ConversationalSearch
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

# Commands

**Development**
```bash
# Full system startup
docker-compose up -d

# Frontend (hexar-frontend/)
npm run dev                     # localhost:3000
npm run build && npm run lint

# Backend (hexar-backend/)
python main.py                  # localhost:8000
python -m agents.consumer_agent --user-id test123

# Agent testing
curl -X POST localhost:8000/agents/consumer/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "message": "Find me a snowboard under $500"}'
```

**Environment (.env)**
```bash
# Backend
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_role_key
GEMINI_API_KEY=your_gemini_key
RABBITMQ_URL=amqp://localhost:5672

# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_AGENT_WEBSOCKET_URL=ws://localhost:8000/agents/ws
```

# Code Style

**Agent Communication Pattern**
```python
# LangChain Consumer Agent
class ConsumerAgent:
    def __init__(self, user_id: str):
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro")
        self.memory = ConversationBufferWindowMemory(k=10)
        self.tools = [
            Tool(name="query_vendors", func=self.query_vendor_agents),
            Tool(name="analyze_products", func=self.analyze_product_data)
        ]
        self.agent = initialize_agent(
            tools=self.tools, llm=self.llm, 
            agent="conversational-react-description",
            memory=self.memory, verbose=True
        )
```

**MCP Message Schema**
```python
class MCPMessage(BaseModel):
    message_id: str
    sender_agent: str
    recipient_agents: List[str]
    message_type: str  # 'search_request', 'search_response'
    payload: Dict[str, Any]
    timestamp: datetime
    timeout_seconds: int = 30
```

**Frontend Agent Communication**
```typescript
interface AgentStore {
  consumerAgent: {
    profile: UserProfile
    conversationHistory: Message[]
    currentQuery: SearchQuery | null
  }
  vendorAgents: {
    [vendorId: string]: {
      status: 'idle' | 'querying' | 'complete' | 'error'
      results: ProductResult[]
    }
  }
}
```

**Critical Patterns**
- All vendor agents implement fallback strategies
- Agent failures must not crash the system
- TypeScript strict mode for agent interfaces
- Async/await for all agent operations
- Comprehensive error logging with agent tracing

# Do Not Section

**Agent System Critical**
- Agent memory/conversation buffers (LangChain managed)
- MCP message broker routing tables
- Inter-agent authentication tokens
- LLM API keys and quotas

**Vendor Dependencies**
- Site-specific scraping logic (fragile to changes)
- Anti-detection proxy configurations
- CAPTCHA solving service credentials
- Browser automation scripts

**Database & State**
- Agent conversation histories (privacy sensitive)
- User preference learning data
- Production agent deployment configs
- Message broker clustering setup

---

**🎯 Key Risk: Vendor Agent Dependencies**

E-commerce sites constantly change structure and implement anti-bot protection. Mitigation:
1. **Multiple data sources**: Affiliate APIs, product feeds, community sources
2. **Fallback hierarchy**: API → Headless browser → HTTP scraping → Cached data → AI estimates
3. **Fault tolerance**: System works with partial vendor failures
4. **Graceful degradation**: Users get results even when some agents fail

**🔧 Architecture Benefits**
- **Modularity**: Each agent is independent and replaceable
- **Scalability**: Agents can run on separate containers/servers  
- **Resilience**: Distributed system survives individual component failures
- **Experimentation**: Easy to test new agent behaviors and data sources