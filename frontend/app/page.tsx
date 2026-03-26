import { Nav } from "@/components/Nav";

export default function Home() {
  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            AG-UI Demo
          </h1>
          <p className="text-sm mb-6">
            Two CopilotKit pages, each connected to a different AG-UI backend
            agent. Zero AI on the frontend — all LLM calls go through the Python
            backend.
          </p>
          <div className="flex gap-4 justify-center">
            <a
              href="/chat"
              className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-700"
            >
              Chat Agent
            </a>
            <a
              href="/segment"
              className="rounded-lg bg-purple-600 px-6 py-3 text-sm font-medium text-white hover:bg-purple-700"
            >
              Segment Builder
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
