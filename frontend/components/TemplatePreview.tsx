interface TemplatePreviewProps {
  html: string;
  css: string;
}

export function TemplatePreview({ html, css }: TemplatePreviewProps) {
  const fullHtml = `<!DOCTYPE html><html><head><style>${css}</style></head><body style="margin:0;padding:20px;background:#f5f5f5;">${html || '<p style="text-align:center;color:#999;padding:40px;">Preview will appear here</p>'}</body></html>`;

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
        <span className="text-xs font-medium text-gray-500">Preview</span>
      </div>
      <iframe
        srcDoc={fullHtml}
        className="flex-1 w-full bg-white"
        sandbox="allow-same-origin"
        title="Template Preview"
      />
    </div>
  );
}
