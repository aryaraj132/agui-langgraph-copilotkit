# All-Purpose Chat Agent

## AG-UI Concepts Demonstrated

### Middleware
Three middleware layers applied in the event pipeline:
1. `LoggingMiddleware` — logs every event type for debugging
2. `CapabilityFilterMiddleware` — filters events to only allowed types
3. `HistoryMiddleware` — stores all events in ThreadStore

Middleware composes via async generators: `Logging(CapabilityFilter(History(raw_stream)))`

### Capabilities
Agent declares its capabilities via `GET /api/v1/agents/capabilities`:
```json
{"streaming": true, "state": false, "tools": true, "reasoning": false, "multi_agent": true}
```
Frontend can query this to adapt UI features.

### Backend-Defined Tools (vs Frontend-Defined)
Three LangGraph `@tool` functions executed server-side:
- `generate_segment(description)` — calls the Segment Generator agent
- `create_template(brief)` — calls the Template Creator agent
- `generate_custom_property(description)` — calls the Custom Property Generator

These differ from template's frontend tools:
| | Backend Tools (Chat) | Frontend Tools (Template) |
|---|---|---|
| **Defined in** | Python `@tool` decorator | JSON schemas in `tools.py` |
| **Executed by** | Backend (LangGraph) | Frontend (`useCopilotAction`) |
| **Events** | `TOOL_CALL_START/ARGS/END` for transparency | `TOOL_CALL_START/ARGS/END` for execution |
| **Result** | Tool returns to agent directly | Frontend returns `TOOL_CALL_RESULT` |

### Multi-Agent Orchestration
Chat agent calls other agents as tools, creating a hub-and-spoke pattern.

### Messages
Demonstrates all message types:
- User messages (input)
- Assistant messages (streaming text)
- Tool messages (tool call results from backend tools)

## Files
- `graph.py` — `create_react_agent` with tools list
- `tools.py` — Backend `@tool` functions that invoke other agent graphs
- `routes.py` — Streaming with tool call event detection and middleware chain
