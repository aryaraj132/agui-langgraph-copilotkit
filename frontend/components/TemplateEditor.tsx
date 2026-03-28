"use client";

import { useState } from "react";
import type { EmailTemplate } from "@/lib/types";
import { TemplatePreview } from "./TemplatePreview";

interface TemplateEditorProps {
  template: EmailTemplate;
  onHtmlChange?: (html: string) => void;
}

export function TemplateEditor({ template, onHtmlChange }: TemplateEditorProps) {
  const [showSource, setShowSource] = useState(false);
  const [localHtml, setLocalHtml] = useState(template.html);

  // Sync when template changes from agent
  const [prevVersion, setPrevVersion] = useState(template.version);
  if (template.version !== prevVersion) {
    setLocalHtml(template.html);
    setPrevVersion(template.version);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Metadata bar */}
      <div className="flex items-center gap-4 px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 truncate">
          {template.subject || "Untitled"}
        </h3>
        {template.preview_text && (
          <span className="text-xs text-gray-500 truncate hidden sm:inline">
            {template.preview_text}
          </span>
        )}
        <span className="text-xs text-gray-400 ml-auto shrink-0">
          v{template.version}
        </span>
        <button
          onClick={() => setShowSource(!showSource)}
          className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors shrink-0"
        >
          {showSource ? "Hide Source" : "Edit Source"}
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 flex min-h-0">
        {showSource && (
          <div className="w-1/2 flex flex-col border-r border-gray-200 dark:border-gray-700">
            <div className="px-3 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              <span className="text-xs font-medium text-gray-500">HTML Source</span>
            </div>
            <textarea
              className="flex-1 w-full p-3 text-xs font-mono bg-white dark:bg-gray-950 text-gray-800 dark:text-gray-200 resize-none focus:outline-none"
              value={localHtml}
              onChange={(e) => {
                setLocalHtml(e.target.value);
                onHtmlChange?.(e.target.value);
              }}
              spellCheck={false}
            />
          </div>
        )}
        <div className={showSource ? "w-1/2" : "w-full"}>
          <TemplatePreview html={showSource ? localHtml : template.html} css={template.css} />
        </div>
      </div>
    </div>
  );
}
