"use client";

import { Suspense, useEffect } from "react";
import {
  CopilotKit,
  useCoAgentStateRender,
  useCoAgent,
} from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { CampaignBuilder } from "@/components/CampaignBuilder";
import { AgentHistoryPanel } from "@/components/AgentHistoryPanel";
import { useAgentThread } from "@/hooks/useAgentThread";
import { useRestoreThread } from "@/hooks/useRestoreThread";
import type { Campaign } from "@/lib/types";

function CampaignPageContent({ threadId, isExistingThread }: { threadId: string; isExistingThread: boolean }) {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.name ? <CampaignBuilder campaign={state} /> : null,
  });

  const { state: campaign, setState: setCampaign } = useCoAgent<Campaign>({
    name: "default",
  });

  const { threadData } = useRestoreThread(threadId, isExistingThread);

  // Restore agent state — campaign is stored nested under "campaign" key
  useEffect(() => {
    const saved = threadData?.state?.campaign;
    if (saved && typeof saved === "object" && (saved as Record<string, unknown>).name) {
      setCampaign(saved as unknown as Campaign);
    }
  }, [threadData, setCampaign]);

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center p-8">
        {campaign?.name ? (
          <div className="w-full max-w-lg">
            <CampaignBuilder campaign={campaign} />
          </div>
        ) : (
          <p className="text-sm text-gray-400">
            Describe your email campaign in the sidebar.
          </p>
        )}
      </main>
    </div>
  );
}

function CampaignPageInner() {
  const { threadId, isExistingThread, ready, startNewThread, switchToThread } = useAgentThread();

  return (
    <>
      <AgentHistoryPanel
        agentType="campaign"
        currentThreadId={threadId}
        onNewThread={startNewThread}
        onSelectThread={switchToThread}
      />
      {ready ? (
        <CopilotKit
          key={threadId}
          runtimeUrl="/api/copilotkit/campaign"
          threadId={threadId}
        >
          <CopilotSidebar
            defaultOpen={true}
            instructions="You are an email campaign builder. Help the user create campaign definitions."
            labels={{
              title: "Campaign Builder",
              initial:
                'Describe the campaign you want to create.\n\nTry: **"A spring sale campaign targeting active US users"**',
            }}
          >
            <CampaignPageContent threadId={threadId} isExistingThread={isExistingThread} />
          </CopilotSidebar>
        </CopilotKit>
      ) : null}
    </>
  );
}

export default function CampaignPage() {
  return (
    <Suspense>
      <CampaignPageInner />
    </Suspense>
  );
}
