"use client";

import { Suspense, useEffect } from "react";
import {
  CopilotKit,
  useCoAgentStateRender,
  useCoAgent,
} from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { SegmentCard } from "@/components/SegmentCard";
import { AgentHistoryPanel } from "@/components/AgentHistoryPanel";
import { useAgentThread } from "@/hooks/useAgentThread";
import { useRestoreThread } from "@/hooks/useRestoreThread";
import type { Segment } from "@/lib/types";

function SegmentPageContent({ threadId, isExistingThread }: { threadId: string; isExistingThread: boolean }) {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.condition_groups ? <SegmentCard segment={state} /> : null,
  });

  const { state: segment, setState: setSegment } = useCoAgent<Segment>({
    name: "default",
  });

  const { threadData } = useRestoreThread(threadId, isExistingThread);

  // Restore agent state from thread
  useEffect(() => {
    if (threadData?.state && threadData.state.name) {
      setSegment(threadData.state as unknown as Segment);
    }
  }, [threadData, setSegment]);

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center p-8">
        {segment?.condition_groups ? (
          <div className="w-full max-w-lg">
            <SegmentCard segment={segment} />
          </div>
        ) : (
          <p className="text-sm text-gray-400">
            Describe your audience in the sidebar to generate a segment.
          </p>
        )}
      </main>
    </div>
  );
}

function SegmentPageInner() {
  const { threadId, isExistingThread, ready, startNewThread, switchToThread } = useAgentThread();

  return (
    <>
      <AgentHistoryPanel
        agentType="segment"
        currentThreadId={threadId}
        onNewThread={startNewThread}
        onSelectThread={switchToThread}
      />
      {ready ? (
        <CopilotKit
          key={threadId}
          runtimeUrl="/api/copilotkit/segment"
          threadId={threadId}
        >
          <CopilotSidebar
            defaultOpen={true}
            instructions="You are a user segmentation assistant. The user will describe a target audience and you will generate a structured segment definition with conditions. Available fields include: age, gender, country, city, signup_date, plan_type, purchase_count, total_spent, login_count, email_opened, email_clicked, app_opens, feature_used. Available operators: equals, not_equals, greater_than, less_than, contains, within_last, before, after, between, is_set, is_not_set, in, not_in."
            labels={{
              title: "Segment Builder",
              initial:
                "Describe your target audience and I'll generate a structured segment.\n\nTry: **\"Users from the US who signed up in the last 30 days and made a purchase\"**",
            }}
          >
            <SegmentPageContent threadId={threadId} isExistingThread={isExistingThread} />
          </CopilotSidebar>
        </CopilotKit>
      ) : null}
    </>
  );
}

export default function SegmentPage() {
  return (
    <Suspense>
      <SegmentPageInner />
    </Suspense>
  );
}
