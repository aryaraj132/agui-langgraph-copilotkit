import Link from "next/link";
import { Nav } from "@/components/Nav";

const agents = [
  {
    href: "/chat",
    title: "All-Purpose Chat",
    description: "Multi-agent orchestrator with backend tools.",
    concepts: ["Middleware", "Capabilities", "BE Tools", "Multi-Agent"],
  },
  {
    href: "/segment",
    title: "Segment Builder",
    description: "Generate audience segments with structured output.",
    concepts: ["Events", "State Snapshots", "Messages", "Serialization"],
  },
  {
    href: "/template",
    title: "Template Creator",
    description: "Collaborative email template editor.",
    concepts: ["State Deltas", "FE Tools", "Activity", "Reasoning"],
  },
  {
    href: "/campaign",
    title: "Campaign Builder",
    description: "Compose segments and templates into campaigns.",
    concepts: ["Multi-Agent State"],
  },
  {
    href: "/custom-property",
    title: "Custom Properties",
    description: "Generate computed properties with JavaScript.",
    concepts: ["Custom Events", "Generative UI"],
  },
];

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            AG-UI Core Concepts Demo
          </h1>
          <p className="text-sm text-gray-500 mb-8">
            Email marketing AI assistant demonstrating all 11 AG-UI protocol
            concepts.
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map(({ href, title, description, concepts }) => (
              <Link
                key={href}
                href={href}
                className="block p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 hover:shadow-sm transition-all bg-white dark:bg-gray-900"
              >
                <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                  {title}
                </h2>
                <p className="text-xs text-gray-500 mb-3">{description}</p>
                <div className="flex flex-wrap gap-1">
                  {concepts.map((c) => (
                    <span
                      key={c}
                      className="text-xs bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 px-2 py-0.5 rounded-full"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
