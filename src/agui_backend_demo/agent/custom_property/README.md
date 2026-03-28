# Custom Property Generator Agent (Stub)

## AG-UI Concepts Demonstrated

### Custom Events
- `CUSTOM` event with name `"property_generated"` and metadata value
- Custom events enable application-specific event types beyond the standard AG-UI protocol
- Frontend can listen for these to trigger custom UI behaviors

### Generative UI Concepts
The agent generates both:
1. A structured property definition (name, type, description)
2. Executable JavaScript code

This demonstrates the generative UI pattern where agents produce dynamic UI content
(in this case, a code editor component) rather than just text responses.

## Custom Event Payload
```json
{
  "type": "CUSTOM",
  "name": "property_generated",
  "value": {
    "property_name": "days_since_signup",
    "property_type": "number",
    "has_code": true
  }
}
```

## Files
- `graph.py` — Single-node graph with structured output for CustomProperty
- `state.py` — `CustomPropertyState` TypedDict
- `routes.py` — SSE lifecycle with CUSTOM event emission
