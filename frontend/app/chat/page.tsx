"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";

export default function ChatPage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit/chat">
      <CopilotSidebar
        defaultOpen={true}
        labels={{
          title: "Chat",
          initial:
            "Hi! I'm powered by Claude, running on the AG-UI backend.\nNo AI on the frontend — ask me anything!",
        }}
      >
        <div className="h-screen flex flex-col">
          <Nav />
          <main className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center max-w-md">
              <p className="text-lg mb-2">Chat Agent</p>
              <p className="text-sm">
                CopilotKit sidebar connected to the backend chat agent via
                AG-UI protocol. All LLM calls happen on the Python backend.
              </p>
            </div>
          </main>
        </div>
      </CopilotSidebar>
    </CopilotKit>
  );
}
