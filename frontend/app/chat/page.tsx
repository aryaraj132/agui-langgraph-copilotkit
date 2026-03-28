"use client";

import { Suspense } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { AgentHistoryPanel } from "@/components/AgentHistoryPanel";
import { useAgentThread } from "@/hooks/useAgentThread";
import { useRestoreThread } from "@/hooks/useRestoreThread";

function ChatPageContent({ threadId, isExistingThread }: { threadId: string; isExistingThread: boolean }) {
  useRestoreThread(threadId, isExistingThread);

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center max-w-md">
          <p className="text-lg mb-2">Chat Agent</p>
          <p className="text-sm">
            CopilotKit sidebar connected to the backend chat agent via AG-UI
            protocol. All LLM calls happen on the Python backend.
          </p>
        </div>
      </main>
    </div>
  );
}

function ChatPageInner() {
  const { threadId, isExistingThread, ready, startNewThread, switchToThread } = useAgentThread();

  return (
    <>
      <AgentHistoryPanel
        agentType="chat"
        currentThreadId={threadId}
        onNewThread={startNewThread}
        onSelectThread={switchToThread}
      />
      {ready ? (
        <CopilotKit
          key={threadId}
          runtimeUrl="/api/copilotkit/chat"
          threadId={threadId}
        >
          <CopilotSidebar
            defaultOpen={true}
            labels={{
              title: "Chat",
              initial:
                "Hi! I'm powered by Claude, running on the AG-UI backend.\nNo AI on the frontend — ask me anything!",
            }}
          >
            <ChatPageContent threadId={threadId} isExistingThread={isExistingThread} />
          </CopilotSidebar>
        </CopilotKit>
      ) : null}
    </>
  );
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatPageInner />
    </Suspense>
  );
}
