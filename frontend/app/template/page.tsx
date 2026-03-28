"use client";

import { Suspense, useEffect, useRef } from "react";
import {
  CopilotKit,
  useCoAgentStateRender,
  useCoAgent,
} from "@copilotkit/react-core";
import {
  CopilotSidebar,
  RenderMessageProps,
  AssistantMessage as DefaultAssistantMessage,
  UserMessage as DefaultUserMessage,
  ImageRenderer as DefaultImageRenderer,
} from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { TemplateEditor } from "@/components/TemplateEditor";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { ActivityIndicator } from "@/components/ActivityIndicator";
import { AgentHistoryPanel } from "@/components/AgentHistoryPanel";
import { useAgentThread } from "@/hooks/useAgentThread";
import { useRestoreThread } from "@/hooks/useRestoreThread";
import type { EmailTemplate } from "@/lib/types";

function CustomRenderMessage({
  message,
  messages,
  inProgress,
  index,
  isCurrentMessage,
  AssistantMessage = DefaultAssistantMessage,
  UserMessage = DefaultUserMessage,
  ImageRenderer = DefaultImageRenderer,
}: RenderMessageProps) {
  if (message.role === "reasoning" || message.role === "activity") {
    // Hide when no run is active
    if (!inProgress) return null;
    // Hide if this belongs to a completed turn (an assistant message with
    // content exists after it in the list)
    const fromOldTurn = messages
      .slice(index + 1)
      .some((m) => m.role === "assistant" && m.content);
    if (fromOldTurn) return null;

    if (message.role === "reasoning") {
      return <ReasoningPanel reasoning={message.content} defaultOpen />;
    }
    return (
      <ActivityIndicator
        activityType={(message as any).activityType ?? "processing"}
        content={message.content as any}
      />
    );
  }

  if (message.role === "user") {
    return <UserMessage key={index} rawData={message} message={message} ImageRenderer={ImageRenderer} />;
  }

  if (message.role === "assistant") {
    return (
      <AssistantMessage
        key={index}
        rawData={message}
        message={message}
        isLoading={inProgress && isCurrentMessage && !message.content}
        isGenerating={inProgress && isCurrentMessage && !!message.content}
        isCurrentMessage={isCurrentMessage}
      />
    );
  }

  return null;
}

function TemplatePageContent({ threadId, isExistingThread }: { threadId: string; isExistingThread: boolean }) {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.subject ? (
        <div className="my-2 p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs text-green-700 dark:text-green-300">
          Template updated: {state.subject}
        </div>
      ) : null,
  });

  const { state: template, setState: setTemplate } =
    useCoAgent<EmailTemplate>({ name: "default" });

  const setTemplateRef = useRef(setTemplate);
  setTemplateRef.current = setTemplate;

  const { threadData } = useRestoreThread(threadId, isExistingThread);

  // Restore agent state — template is stored nested under "template" key
  useEffect(() => {
    const saved = threadData?.state?.template;
    if (saved && typeof saved === "object" && (saved as Record<string, unknown>).subject) {
      setTemplateRef.current(saved as unknown as EmailTemplate);
    }
  }, [threadData]);

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 overflow-hidden">
        {template?.subject ? (
          <TemplateEditor
            template={template}
            onHtmlChange={(html) => setTemplate({ ...template, html })}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-gray-400">
              Describe your email template in the sidebar to get started.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

function TemplatePageInner() {
  const { threadId, isExistingThread, ready, startNewThread, switchToThread } = useAgentThread();

  return (
    <>
      <AgentHistoryPanel
        agentType="template"
        currentThreadId={threadId}
        onNewThread={startNewThread}
        onSelectThread={switchToThread}
      />
      {ready ? (
        <CopilotKit
          key={threadId}
          runtimeUrl="/api/copilotkit/template"
          threadId={threadId}
        >
          <CopilotSidebar
            defaultOpen={true}
            RenderMessage={CustomRenderMessage}
            instructions="You are an email template design assistant. Help the user create and modify professional HTML email templates."
            labels={{
              title: "Template Creator",
              initial:
                'Describe the email template you want to create.\n\nTry: **"A welcome email for new SaaS users with a hero image and CTA button"**',
            }}
          >
            <TemplatePageContent threadId={threadId} isExistingThread={isExistingThread} />
          </CopilotSidebar>
        </CopilotKit>
      ) : null}
    </>
  );
}

export default function TemplatePage() {
  return (
    <Suspense>
      <TemplatePageInner />
    </Suspense>
  );
}
