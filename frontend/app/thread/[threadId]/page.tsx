"use client";

import { useParams } from "next/navigation";
import { Nav } from "@/components/Nav";
import { useThreadMessages } from "@/hooks/useThreadHistory";

export default function ThreadPage() {
  const params = useParams();
  const threadId = params.threadId as string;
  const { messages, threadData, loading, error } =
    useThreadMessages(threadId);

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Thread: {threadId}
            </h1>
            {threadData && (
              <p className="text-xs text-gray-500 mt-1">
                Agent: {threadData.agent_type} | Created:{" "}
                {new Date(threadData.created_at).toLocaleString()}
              </p>
            )}
          </div>
          {loading && <p className="text-sm text-gray-400">Loading...</p>}
          {error && <p className="text-sm text-red-500">Error: {error}</p>}
          <div className="space-y-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg text-sm ${
                  msg.role === "user"
                    ? "bg-blue-50 dark:bg-blue-900/20 ml-8"
                    : "bg-gray-50 dark:bg-gray-800 mr-8"
                }`}
              >
                <span className="text-xs font-medium text-gray-500 block mb-1">
                  {msg.role}
                </span>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {msg.content}
                </p>
              </div>
            ))}
            {messages.length === 0 && !loading && (
              <p className="text-sm text-gray-400 text-center py-8">
                No messages in this thread.
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
