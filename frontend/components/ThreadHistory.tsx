"use client";

import Link from "next/link";
import { useThreadHistory } from "@/hooks/useThreadHistory";

const agentLabels: Record<string, string> = {
  chat: "Chat",
  segment: "Segment",
  template: "Template",
  campaign: "Campaign",
  custom_property: "Custom Property",
};

export function ThreadHistory() {
  const { threads, loading, error, refetch } = useThreadHistory();
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Thread History
        </span>
        <button
          onClick={refetch}
          className="text-xs text-blue-500 hover:text-blue-700"
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>
      {error && (
        <div className="px-4 py-2 text-xs text-red-500">Error: {error}</div>
      )}
      <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-80 overflow-y-auto">
        {threads.length === 0 ? (
          <p className="px-4 py-3 text-xs text-gray-400">No threads yet</p>
        ) : (
          threads.map((thread) => (
            <Link
              key={thread.id}
              href={`/thread/${thread.id}`}
              className="block px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {agentLabels[thread.agent_type] || thread.agent_type}
                </span>
                <span className="text-xs text-gray-400">
                  {thread.message_count} msg
                  {thread.message_count !== 1 ? "s" : ""}
                </span>
              </div>
              <p className="text-xs text-gray-400 truncate">{thread.id}</p>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
