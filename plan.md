Can you implement all the core concepts of AG-UI in this project for better understanding,
* New concepts which are not yet implemented should be implemented in their separate folder in both backend and frontend.
* For the concepts which are already implemented such as few of the events are implemented, extend the implementation in the existing folder structure.
* Create a detailed documentation of the contract of each concept in their sub-folders for both backend and frontend.
* For content and use case to build these concepts, assume you are an email marketing platform and you are building an ai assistant in your system which can work with human hand-in-hand in following area:
  1. Segment Generation
  2. Template Creator (here human and AI will together create the template so both can make change to template one by one)
  3. Email campaign builder (use both 1 and 2 and generate other elements of a campaign)
  4. Custom properties generator (generate a custom property and a javascript code corresponding to it)
  5. All purpose chat interface, which can call these other agents as well.

Here is the list of core concepts of AG-UI that you need to implement:
https://docs.ag-ui.com/concepts/architecture
https://docs.ag-ui.com/concepts/events
https://docs.ag-ui.com/concepts/agents
https://docs.ag-ui.com/concepts/middleware
https://docs.ag-ui.com/concepts/messages
https://docs.ag-ui.com/concepts/reasoning
https://docs.ag-ui.com/concepts/state
https://docs.ag-ui.com/concepts/serialization
https://docs.ag-ui.com/concepts/tools
https://docs.ag-ui.com/concepts/capabilities
https://docs.ag-ui.com/concepts/generative-ui-specs

Also address these concerns and questions:
1. What are Tool call from FE Vs Tool Call from BE in AG-UI?
2. History management in copilotkit → sync history from BE to frontend and how to handle delta and incremental updates?
3. mock **Activity Events** in this poc
4. Diff b/w activity event and reasoning

Restrictions to adhere:
1. Frontend can not make any llm calls, all calls will go to backend and backend will make llm calls
2. Make sure every history is saved in backend(for this purpose in-memory), and frontend should fetch conversation history as well as conversation of any particular thread from backend
3. Make sure ever conversation corresponds to a threadId and we can go to those threadId's from Url, and we can reload, close and re-open the browser but the conversation should persist
