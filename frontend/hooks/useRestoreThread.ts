"use client";

import { useState, useEffect, useRef } from "react";
import { useCopilotMessagesContext } from "@copilotkit/react-core";
import { TextMessage, Role } from "@copilotkit/runtime-client-gql";
import type { ThreadData } from "@/lib/types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export function useRestoreThread(threadId: string, isExistingThread = true) {
  const { setMessages } = useCopilotMessagesContext();
  const setMessagesRef = useRef(setMessages);
  setMessagesRef.current = setMessages;

  const [threadData, setThreadData] = useState<ThreadData | null>(null);
  const [isRestoring, setIsRestoring] = useState(isExistingThread);

  useEffect(() => {
    setThreadData(null);

    if (!isExistingThread) {
      setIsRestoring(false);
      return;
    }

    let cancelled = false;

    async function restore() {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/threads/${threadId}`);
        if (!res.ok) {
          // Thread doesn't exist yet (new conversation)
          return;
        }
        const data: ThreadData = await res.json();
        if (cancelled) return;

        setThreadData(data);

        // Restore messages into CopilotKit
        if (data.messages?.length > 0) {
          const msgs = data.messages.map(
            (m) =>
              new TextMessage({
                id: crypto.randomUUID(),
                content: m.content || "",
                role: m.role === "user" ? Role.User : Role.Assistant,
              }),
          );
          setMessagesRef.current(msgs);
        }
      } catch (e) {
        console.error("Failed to restore thread:", e);
      } finally {
        if (!cancelled) setIsRestoring(false);
      }
    }

    restore();
    return () => {
      cancelled = true;
    };
  }, [threadId, isExistingThread]);

  return { threadData, isRestoring };
}
