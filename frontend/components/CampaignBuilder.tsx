import type { Campaign } from "@/lib/types";

export function CampaignBuilder({ campaign }: { campaign: Campaign }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden text-sm my-2 w-full">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {campaign.name}
          </span>
          <span
            className={`shrink-0 text-xs px-2 py-0.5 rounded-full ${
              campaign.status === "draft"
                ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                : campaign.status === "scheduled"
                  ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                  : "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
            }`}
          >
            {campaign.status}
          </span>
        </div>
      </div>
      <div className="px-4 py-3 space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Subject:</span>
          <span className="text-gray-700 dark:text-gray-300">
            {campaign.subject || "\u2014"}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Segment:</span>
          <span className="text-gray-700 dark:text-gray-300">
            {campaign.segment_id || "Not set"}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Template:</span>
          <span className="text-gray-700 dark:text-gray-300">
            {campaign.template_id || "Not set"}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Send Time:</span>
          <span className="text-gray-700 dark:text-gray-300">
            {campaign.send_time || "Not scheduled"}
          </span>
        </div>
      </div>
    </div>
  );
}
