# Architecture Diagrams - AI PowerPoint Generator

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js UI]
        Auth[Auth Context]
        Services[API Services]
    end
    
    subgraph "Backend Layer"
        API[FastAPI Server]
        Middleware[JWT Middleware]
        Validation[Request Validation]
    end
    
    subgraph "Business Logic"
        Orchestrator[LLM Orchestrator]
        PPTGen[PPT Generator]
    end
    
    subgraph "Multi-Agent Pipeline"
        Planner[Planner Agent]
        Content[Content Agent]
        Reviewer[Reviewer Agent]
        Design[Design Agent]
    end
    
    subgraph "External Services"
        Ollama[Ollama Server]
        Mistral[Mistral 7B Model]
    end
    
    subgraph "Storage"
        DB[(SQLite DB)]
        Files[Temp Files]
    end
    
    UI --> Services
    Services --> API
    API --> Middleware
    Middleware --> Validation
    Validation --> Orchestrator
    
    Orchestrator --> Planner
    Planner --> Content
    Content --> Reviewer
    Reviewer --> Design
    
    Planner -.->|LLM Calls| Ollama
    Content -.->|LLM Calls| Ollama
    Reviewer -.->|LLM Calls| Ollama
    Design -.->|LLM Calls| Ollama
    
    Ollama --> Mistral
    
    Design --> PPTGen
    PPTGen --> Files
    
    Middleware --> DB
    Auth --> DB
    
    style Orchestrator fill:#6366f1,color:#fff
    style Planner fill:#8b5cf6,color:#fff
    style Content fill:#8b5cf6,color:#fff
    style Reviewer fill:#8b5cf6,color:#fff
    style Design fill:#8b5cf6,color:#fff
```

## Multi-Agent Pipeline Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Orchestrator
    participant Planner
    participant Content
    participant Reviewer
    participant Design
    participant Ollama
    participant PPTGen
    
    User->>Frontend: Enter topic, tone, slides
    Frontend->>API: POST /api/presentations/generate
    API->>Orchestrator: generate_presentation_content()
    
    Note over Orchestrator: Start Pipeline (420s timeout)
    
    Orchestrator->>Planner: generate_outline()
    Planner->>Ollama: Create outline prompt
    Ollama-->>Planner: SlideOutline JSON
    Planner-->>Orchestrator: SlideOutline
    
    Orchestrator->>Content: generate_content()
    Content->>Ollama: Generate bullets prompt
    Ollama-->>Content: GeneratedContent JSON
    Content-->>Orchestrator: GeneratedContent
    
    Orchestrator->>Reviewer: review_content()
    Reviewer->>Ollama: Review & refine prompt
    Ollama-->>Reviewer: ReviewedContent JSON
    Reviewer-->>Orchestrator: ReviewedContent
    
    Orchestrator->>Design: assign_design()
    Design->>Ollama: Assign layouts prompt
    Ollama-->>Design: DesignedContent JSON
    Design-->>Orchestrator: DesignedContent
    
    Orchestrator->>PPTGen: create_presentation()
    PPTGen-->>Orchestrator: .pptx bytes
    
    Orchestrator-->>API: PresentationContent
    API-->>Frontend: {presentationId, filename, downloadUrl}
    Frontend->>API: GET /api/presentations/download/{id}
    API-->>Frontend: .pptx file
    Frontend-->>User: Download presentation
```

## LangChain Agent Architecture

```mermaid
graph LR
    subgraph "Planner Agent"
        P1[Prompt Template]
        P2[LLM Chain]
        P3[Output Parser]
        P4[Retry Logic]
        
        P1 --> P2
        P2 --> P3
        P3 --> P4
    end
    
    subgraph "Content Agent"
        C1[Prompt Template]
        C2[LLM Chain]
        C3[Output Parser]
        C4[Validation]
        
        C1 --> C2
        C2 --> C3
        C3 --> C4
    end
    
    subgraph "Reviewer Agent"
        R1[Prompt Template]
        R2[LLM Chain]
        R3[Output Parser]
        R4[Quality Check]
        
        R1 --> R2
        R2 --> R3
        R3 --> R4
    end
    
    subgraph "Design Agent"
        D1[Prompt Template]
        D2[LLM Chain]
        D3[Output Parser]
        D4[Layout Assignment]
        
        D1 --> D2
        D2 --> D3
        D3 --> D4
    end
    
    P4 --> C1
    C4 --> R1
    R4 --> D1
    
    style P1 fill:#e0e7ff
    style C1 fill:#e0e7ff
    style R1 fill:#e0e7ff
    style D1 fill:#e0e7ff
```

## Data Flow Diagram

```mermaid
flowchart TD
    Start([User Input]) --> Input{Input Data}
    Input -->|Topic| T[Topic: String]
    Input -->|Tone| Tone[Tone: Enum]
    Input -->|Slides| Count[Slide Count: Int]
    
    T --> Orch[Orchestrator]
    Tone --> Orch
    Count --> Orch
    
    Orch --> P[Planner Agent]
    P --> POut[SlideOutline]
    
    POut --> C[Content Agent]
    C --> COut[GeneratedContent]
    
    COut --> R[Reviewer Agent]
    R --> ROut[ReviewedContent]
    
    ROut --> D[Design Agent]
    D --> DOut[DesignedContent]
    
    DOut --> Agg[Aggregate]
    Agg --> PC[PresentationContent]
    
    PC --> PPT[PPT Generator]
    PPT --> File[.pptx File]
    
    File --> Download([User Download])
    
    style Orch fill:#6366f1,color:#fff
    style P fill:#8b5cf6,color:#fff
    style C fill:#8b5cf6,color:#fff
    style R fill:#8b5cf6,color:#fff
    style D fill:#8b5cf6,color:#fff
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant AuthService
    participant JWT
    participant Database
    
    Note over User,Database: Registration Flow
    User->>Frontend: Enter username & password
    Frontend->>API: POST /api/auth/register
    API->>AuthService: register_user()
    AuthService->>Database: Check username exists
    Database-->>AuthService: Not exists
    AuthService->>AuthService: Hash password (bcrypt)
    AuthService->>Database: Insert user
    AuthService->>JWT: generate_token()
    JWT-->>AuthService: JWT token
    AuthService-->>API: token + user info
    API-->>Frontend: {token, user}
    Frontend->>Frontend: Store token in context
    
    Note over User,Database: Login Flow
    User->>Frontend: Enter credentials
    Frontend->>API: POST /api/auth/login
    API->>AuthService: authenticate_user()
    AuthService->>Database: Get user by username
    Database-->>AuthService: User data
    AuthService->>AuthService: Verify password (bcrypt)
    AuthService->>JWT: generate_token()
    JWT-->>AuthService: JWT token
    AuthService-->>API: token + user info
    API-->>Frontend: {token, user}
    
    Note over User,Database: Protected Request
    User->>Frontend: Generate presentation
    Frontend->>API: POST /api/presentations/generate<br/>(Authorization: Bearer token)
    API->>JWT: decode_jwt(token)
    JWT-->>API: User payload
    API->>API: Process request
    API-->>Frontend: Response
```

## Component Interaction Diagram

```mermaid
graph TB
    subgraph "Frontend Components"
        Page[page.tsx]
        Form[PromptForm]
        Progress[ProgressIndicator]
        Error[ErrorDisplay]
        AuthCtx[AuthContext]
    end
    
    subgraph "Backend Modules"
        Main[main.py]
        AuthMod[auth/]
        APIMod[api/]
        OrchMod[orchestrator/]
        PPTMod[ppt_generator/]
    end
    
    subgraph "Data Models"
        Request[Request Models]
        Response[Response Models]
        Internal[Internal Models]
    end
    
    Page --> Form
    Page --> Progress
    Page --> Error
    Page --> AuthCtx
    
    Form --> Main
    AuthCtx --> Main
    
    Main --> AuthMod
    Main --> APIMod
    Main --> OrchMod
    Main --> PPTMod
    
    Main --> Request
    Main --> Response
    OrchMod --> Internal
    
    style Page fill:#3b82f6,color:#fff
    style Main fill:#6366f1,color:#fff
    style OrchMod fill:#8b5cf6,color:#fff
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Dev[Developer Machine]
        
        subgraph "Frontend Process"
            NextDev[npm run dev<br/>Port 3000]
        end
        
        subgraph "Backend Process"
            FastAPI[python main.py<br/>Port 8000]
        end
        
        subgraph "LLM Service"
            OllamaServ[ollama serve<br/>Port 11434]
            MistralModel[Mistral 7B<br/>4.4 GB]
        end
        
        subgraph "Storage"
            SQLite[(users.db)]
            TempFiles[temp_presentations/]
        end
    end
    
    Dev --> NextDev
    Dev --> FastAPI
    Dev --> OllamaServ
    
    NextDev -.->|HTTP| FastAPI
    FastAPI -.->|HTTP| OllamaServ
    OllamaServ --> MistralModel
    
    FastAPI --> SQLite
    FastAPI --> TempFiles
    
    style NextDev fill:#3b82f6,color:#fff
    style FastAPI fill:#6366f1,color:#fff
    style OllamaServ fill:#8b5cf6,color:#fff
```

## Error Handling Flow

```mermaid
flowchart TD
    Start([Request]) --> Try{Try}
    
    Try -->|Success| Agent[Execute Agent]
    Agent --> Timeout{Timeout?}
    
    Timeout -->|No| Parse{Parse Output}
    Timeout -->|Yes| Fallback[Use Fallback]
    
    Parse -->|Success| Validate{Validate}
    Parse -->|Fail| Retry{Retry?}
    
    Retry -->|Yes| Agent
    Retry -->|No| Error[Raise Error]
    
    Validate -->|Pass| Success([Return Result])
    Validate -->|Fail| Error
    
    Fallback --> Success
    
    Error --> Catch[Error Handler]
    Catch --> UserError[User-Friendly Message]
    UserError --> End([Response])
    
    Success --> End
    
    style Success fill:#10b981,color:#fff
    style Error fill:#ef4444,color:#fff
    style Fallback fill:#f59e0b,color:#fff
```

## Technology Stack Layers

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Next.js 14 + React 18]
        CSS[CSS-in-JS + Variables]
        TS[TypeScript]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Framework]
        Pydantic[Pydantic Validation]
        JWT[JWT Authentication]
    end
    
    subgraph "Business Logic Layer"
        Orchestrator[LLM Orchestrator]
        Agents[Multi-Agent System]
        LangChain[LangChain Framework]
    end
    
    subgraph "Data Layer"
        SQLite[(SQLite Database)]
        FileSystem[File System Storage]
    end
    
    subgraph "AI Layer"
        Ollama[Ollama Runtime]
        Mistral[Mistral 7B Model]
    end
    
    UI --> FastAPI
    FastAPI --> Orchestrator
    Orchestrator --> Agents
    Agents --> LangChain
    LangChain --> Ollama
    Ollama --> Mistral
    
    FastAPI --> SQLite
    FastAPI --> FileSystem
    
    style UI fill:#3b82f6,color:#fff
    style FastAPI fill:#6366f1,color:#fff
    style Orchestrator fill:#8b5cf6,color:#fff
    style Ollama fill:#a855f7,color:#fff
```

---

## Diagram Explanations

### 1. System Architecture
Shows the complete system with all layers and their interactions. Highlights the separation between frontend, backend, business logic, and external services.

### 2. Multi-Agent Pipeline Flow
Sequence diagram showing the exact order of operations from user input to file download, including all agent interactions with Ollama.

### 3. LangChain Agent Architecture
Details the internal structure of each agent, showing how LangChain components (prompts, chains, parsers) work together.

### 4. Data Flow
Illustrates how data transforms as it moves through the pipeline, from simple user input to complex presentation content.

### 5. Authentication Flow
Shows both registration and login flows, plus how JWT tokens are used to protect API endpoints.

### 6. Component Interaction
High-level view of how frontend components interact with backend modules.

### 7. Deployment Architecture
Shows how the application runs in development, with all processes and their ports.

### 8. Error Handling Flow
Demonstrates the robust error handling with retries, fallbacks, and user-friendly messages.

### 9. Technology Stack Layers
Visualizes the technology stack organized by architectural layers.

---

## How to Use These Diagrams in Your Demo

1. **Start with System Architecture** - Give the big picture
2. **Zoom into Multi-Agent Pipeline** - Show the sequential flow
3. **Explain LangChain Agents** - Detail the AI components
4. **Show Data Flow** - Demonstrate data transformation
5. **Highlight Error Handling** - Emphasize robustness

These diagrams are in Mermaid format and can be rendered in:
- GitHub/GitLab markdown
- VS Code with Mermaid extension
- Online tools like mermaid.live
- Presentation tools that support Mermaid
