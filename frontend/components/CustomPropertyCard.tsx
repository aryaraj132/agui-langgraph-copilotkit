import type { CustomProperty } from "@/lib/types";

export function CustomPropertyCard({ property }: { property: CustomProperty }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden text-sm my-2 w-full">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold font-mono text-gray-900 dark:text-gray-100">
            {property.name}
          </span>
          <span className="shrink-0 text-xs bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300 px-2 py-0.5 rounded-full">
            {property.property_type}
          </span>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mt-1 text-xs">
          {property.description}
        </p>
      </div>
      <div className="px-4 py-3">
        <div className="text-xs text-gray-500 mb-1 font-medium">
          JavaScript Code:
        </div>
        <pre className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-xs font-mono text-gray-700 dark:text-gray-300 overflow-x-auto">
          <code>{property.javascript_code}</code>
        </pre>
      </div>
      {property.example_value && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
          Example: <code className="font-mono">{property.example_value}</code>
        </div>
      )}
    </div>
  );
}
