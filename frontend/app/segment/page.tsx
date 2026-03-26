"use client";

import { CopilotKit, useCoAgentStateRender, useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { SegmentCard } from "@/components/SegmentCard";

interface Segment {
  name: string;
  description: string;
  condition_groups: Array<{
    logical_operator: "AND" | "OR";
    conditions: Array<{ field: string; operator: string; value: string | number | string[] }>;
  }>;
  estimated_scope?: string;
}

function SegmentPageContent() {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.condition_groups ? <SegmentCard segment={state} /> : null,
  });

  const { state: segment } = useCoAgent<Segment>({ name: "default" });

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center p-8">
        {segment?.condition_groups ? (
          <div className="w-full max-w-lg">
            <SegmentCard segment={segment} />
          </div>
        ) : (
          <p className="text-sm text-gray-400">
            Describe your audience in the sidebar to generate a segment.
          </p>
        )}
      </main>
    </div>
  );
}

export default function SegmentPage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit/segment">
      <CopilotSidebar
        defaultOpen={true}
        instructions="You are a user segmentation assistant. The user will describe a target audience and you will generate a structured segment definition with conditions. Available fields include: age, gender, country, city, signup_date, plan_type, purchase_count, total_spent, login_count, email_opened, email_clicked, app_opens, feature_used. Available operators: equals, not_equals, greater_than, less_than, contains, within_last, before, after, between, is_set, is_not_set, in, not_in."
        labels={{
          title: "Segment Builder",
          initial:
            "Describe your target audience and I'll generate a structured segment.\n\nTry: **\"Users from the US who signed up in the last 30 days and made a purchase\"**",
        }}
      >
        <SegmentPageContent />
      </CopilotSidebar>
    </CopilotKit>
  );
}
