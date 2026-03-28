"use client";

import { useRef, useEffect } from "react";

interface TemplatePreviewProps {
  html: string;
  css: string;
  editable?: boolean;
  onHtmlChange?: (html: string) => void;
}

export function TemplatePreview({
  html,
  css,
  editable = false,
  onHtmlChange,
}: TemplatePreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  // Tracks the last html emitted by user edits inside the iframe.
  // When the parent feeds this value back as the `html` prop we skip
  // the expensive doc.write() rewrite so the cursor stays in place.
  const userEditHtml = useRef<string | null>(null);
  // Stable ref so the input handler never goes stale.
  const onHtmlChangeRef = useRef(onHtmlChange);
  onHtmlChangeRef.current = onHtmlChange;

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;
    const doc = iframe.contentDocument;
    if (!doc) return;

    // Skip rewrite when the html prop is just the feedback from a user edit
    if (userEditHtml.current !== null && userEditHtml.current === html) {
      return;
    }
    userEditHtml.current = null;

    // Full rewrite — necessary for initial render and agent updates
    doc.open();
    doc.write(
      `<!DOCTYPE html><html><head><style>${css}</style></head>` +
        `<body style="margin:0;padding:20px;background:#f5f5f5;">` +
        `${html || '<p style="text-align:center;color:#999;padding:40px;">Preview will appear here</p>'}` +
        `</body></html>`,
    );
    doc.close();

    if (editable) {
      doc.designMode = "on";
      // Re-attach listener — doc.open() destroys all previous listeners
      doc.addEventListener("input", () => {
        if (!doc.body) return;
        const newHtml = doc.body.innerHTML;
        userEditHtml.current = newHtml;
        onHtmlChangeRef.current?.(newHtml);
      });
    }
  }, [html, css, editable]);

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
        <span className="text-xs font-medium text-gray-500">Preview</span>
        {editable && (
          <span className="text-xs text-blue-500">Click to edit</span>
        )}
      </div>
      <iframe
        ref={iframeRef}
        className="flex-1 w-full bg-white"
        sandbox="allow-same-origin"
        title="Template Preview"
      />
    </div>
  );
}
