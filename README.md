# NemoClaw-Forge

A distributed AI Agent orchestration engine built for high-performance asynchronous execution.

## Architecture

```mermaid
graph TD
    Forge[Forge Master]
    RedisPubSub[(Redis Pub/Sub)]
    Claw1[Claw Worker 1]
    Claw2[Claw Worker 2]
    Brain[Brain Connector]
    Sandbox[Secure Sandbox]
    
    Forge -- Coordinates Tasks & Monitors --> RedisPubSub
    RedisPubSub -- Assigns Tasks & Heartbeats --> Claw1
    RedisPubSub -- Assigns Tasks & Heartbeats --> Claw2
    
    Claw1 --> Sandbox
    Claw2 --> Sandbox
    
    Sandbox --> Brain
    Brain -- Multi-Model Failover --> LLM_Primary[Primary LLM: Nemotron-3]
    Brain -. Fallback .-> LLM_Fallback[Fallback LLM: Gemini/GPT]
```

## Features
- **Multi-Model Failover**: Automatically falls back to secondary models if primary fails.
- **Secure Sandbox**: Execution wrapper for bounded task time and resource limits.
- **Real-time Monitoring**: Redis-backed async pub/sub for agent communication.

## Quickstart

```bash
pip install -e .
nemoclaw forge start
nemoclaw claw start --id worker-1
```
