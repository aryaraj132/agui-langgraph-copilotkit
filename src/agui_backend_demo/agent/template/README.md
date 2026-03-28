# Template Creator Agent

## AG-UI Concepts Demonstrated

### State Deltas (JSON Patch)
- `STATE_SNAPSHOT` — emits full `EmailTemplate` on first generation
- `STATE_DELTA` — emits JSON Patch (RFC 6902) operations on template modifications
- Enables efficient incremental updates without resending entire state
- Operations: `add`, `replace`, `remove` on template fields

### Frontend-Defined Tools
- `update_section` — modifies an existing template section
- `add_section` — adds a new section to the template
- `remove_section` — removes a section from the template
- These are defined in `tools.py` as JSON schemas, NOT LangGraph tools
- Backend emits `TOOL_CALL_START` / `TOOL_CALL_ARGS` / `TOOL_CALL_END` events
- Frontend executes via `useCopilotAction` hook

### Activity Events
- `ACTIVITY_SNAPSHOT` — progress indicators showing what the agent is doing
- Stages: Analyzing (20%) → Generating (50%) → Styling (80%) → Finalizing (100%)
- Displayed as progress bar in frontend

### Reasoning Events
- `REASONING_START` → `REASONING_MESSAGE_START` → `REASONING_MESSAGE_CONTENT` (×N) → `REASONING_MESSAGE_END` → `REASONING_END`
- Shows chain-of-thought: template analysis, layout decisions, design rationale
- Displayed in collapsible ReasoningPanel component

### Human-in-the-Loop
- Bidirectional state: frontend can edit template sections, changes sent back to backend
- Backend reads frontend state to apply AI modifications on top of human edits

## Activity Event vs Reasoning Event
| | Activity Event | Reasoning Event |
|---|---|---|
| **Purpose** | WHAT the agent is doing | WHY/HOW the agent is thinking |
| **Audience** | End user progress updates | Developer/power user insight |
| **Format** | Brief status + progress bar | Detailed chain-of-thought text |
| **UI** | Inline progress indicator | Collapsible panel |
| **Example** | "Generating header section..." | "Single-column layouts render better across email clients..." |

## Files
- `graph.py` — Conditional routing: generate (new) vs modify (existing)
- `state.py` — `TemplateAgentState` with bidirectional version tracking
- `tools.py` — Frontend tool schemas (JSON, not LangGraph)
- `routes.py` — Full event lifecycle with reasoning, activity, state, and tool events
