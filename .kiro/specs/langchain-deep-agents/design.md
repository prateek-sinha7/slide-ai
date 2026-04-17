# Design Document: LangChain Deep Agents with Groq API

## Overview

This design document specifies the technical implementation for replacing the current simple prompt-response chains with true LangChain agents using the ReAct (Reasoning + Acting) pattern. The system will transition from local Ollama inference to cloud-based Groq API for faster execution while implementing autonomous agents with tool usage, reasoning loops, and memory systems.

### Current State

The existing system uses four "agents" (Planner, Content, Reviewer, Designer) that are simple LangChain chains:
- **Pattern**: Prompt → LLM → Parse → Return
- **LLM**: Local Ollama with Mistral model
- **Execution**: Sequential, no iteration or tool usage
- **Memory**: No cross-agent context sharing
- **Decision-making**: None - single-pass generation only

### Target State

The new system implements true LangChain agents with:
- **Pattern**: ReAct (Think → Act → Observe → Repeat)
- **LLM**: Groq API with llama-3.1-70b-versatile or mixtral-8x7b-32768
- **Execution**: Iterative with autonomous tool selection (3-5 iterations max)
- **Memory**: Conversation memory + intermediate result caching
- **Decision-making**: Agents autonomously decide which tools to use and when to stop

### Key Benefits

1. **Autonomous Reasoning**: Agents think through problems and iterate until quality thresholds are met
2. **Tool Usage**: Agents can search the web, validate content, check facts, and more
3. **Faster Inference**: Groq API provides significantly faster model execution than local Ollama
4. **Better Quality**: Iterative refinement with tool feedback produces higher-quality outputs
5. **Observability**: Reasoning traces show agent thought processes and decisions

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "LLM Orchestrator"
        O[Orchestrator]
    end
    
    subgraph "Agent Pipeline"
        P[Planner Agent<br/>ReAct + Tools]
        C[Content Agent<br/>ReAct + Tools]
        R[Reviewer Agent<br/>ReAct + Tools]
        D[Design Agent<br/>ReAct + Tools]
    end
    
    subgraph "Shared Infrastructure"
        G[Groq API<br/>llama-3.1-70b]
        M[Memory System<br/>Conversation + Cache]
        T[Tool Registry<br/>12+ Tools]
    end
    
    subgraph "Tools by Agent"
        PT[Web Search<br/>Structure Validator<br/>Quality Checker]
        CT[Fact Checker<br/>Length Validator<br/>Quality Scorer]
        RT[Grammar Checker<br/>Redundancy Detector<br/>Tone Validator]
        DT[Layout Engine<br/>Balance Checker<br/>Notes Generator]
    end
    
    O --> P
    P --> C
    C --> R
    R --> D
    
    P -.-> G
    C -.-> G
    R -.-> G
    D -.-> G
    
    P --> M
    C --> M
    R --> M
    D --> M
    
    P --> PT
    C --> CT
    R --> RT
    D --> DT
    
    PT --> T
    CT --> T
    RT --> T
    DT --> T
