# Campaign Builder Agent (Stub)

## AG-UI Concepts Demonstrated

### Multi-Agent State Composition
Campaign state combines data from multiple agents:
- `segment` — from Segment Generator
- `template` — from Template Creator
- `campaign` — campaign-specific metadata

In a full implementation, this agent would:
1. Call the Segment Generator to create/select a segment
2. Call the Template Creator to create/select a template
3. Compose them into a campaign with scheduling and delivery settings

### State Snapshots
- `STATE_SNAPSHOT` — emits the complete Campaign as JSON
- Campaign schema: name, segment_id, template_id, subject, send_time, status

## Files
- `graph.py` — Single-node graph with structured output
- `state.py` — `CampaignState` with segment and template slots
- `routes.py` — Standard SSE lifecycle with state snapshot
