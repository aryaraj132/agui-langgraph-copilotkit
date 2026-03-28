"use client";

import { Suspense, useEffect } from "react";
import {
  CopilotKit,
  useCoAgentStateRender,
  useCoAgent,
} from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { CustomPropertyCard } from "@/components/CustomPropertyCard";
import { AgentHistoryPanel } from "@/components/AgentHistoryPanel";
import { useAgentThread } from "@/hooks/useAgentThread";
import { useRestoreThread } from "@/hooks/useRestoreThread";
import type { CustomProperty } from "@/lib/types";

function CustomPropertyPageContent({ threadId, isExistingThread }: { threadId: string; isExistingThread: boolean }) {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.name ? <CustomPropertyCard property={state} /> : null,
  });

  const { state: property, setState: setProperty } =
    useCoAgent<CustomProperty>({ name: "default" });

  const { threadData } = useRestoreThread(threadId, isExistingThread);

  // Restore agent state — stored nested under "custom_property" key
  useEffect(() => {
    const saved = threadData?.state?.custom_property;
    if (saved && typeof saved === "object" && (saved as Record<string, unknown>).name) {
      setProperty(saved as unknown as CustomProperty);
    }
  }, [threadData, setProperty]);

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center p-8">
        {property?.name ? (
          <div className="w-full max-w-lg">
            <CustomPropertyCard property={property} />
          </div>
        ) : (
          <p className="text-sm text-gray-400">
            Describe the custom property you want in the sidebar.
          </p>
        )}
      </main>
    </div>
  );
}

function CustomPropertyPageInner() {
  const { threadId, isExistingThread, ready, startNewThread, switchToThread } = useAgentThread();

  return (
    <>
      <AgentHistoryPanel
        agentType="custom_property"
        currentThreadId={threadId}
        onNewThread={startNewThread}
        onSelectThread={switchToThread}
      />
      {ready ? (
        <CopilotKit
          key={threadId}
          runtimeUrl="/api/copilotkit/custom-property"
          threadId={threadId}
        >
          <CopilotSidebar
            defaultOpen={true}
            instructions="You are a custom property generator. Help create computed user properties with JavaScript code."
            labels={{
              title: "Custom Properties",
              initial:
                'Describe the custom property you want.\n\nTry: **"A boolean property that identifies power users who logged in 30+ times"**',
            }}
          >
            <CustomPropertyPageContent threadId={threadId} isExistingThread={isExistingThread} />
          </CopilotSidebar>
        </CopilotKit>
      ) : null}
    </>
  );
}

export default function CustomPropertyPage() {
  return (
    <Suspense>
      <CustomPropertyPageInner />
    </Suspense>
  );
}
