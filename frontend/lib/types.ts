export interface Condition {
  field: string;
  operator: string;
  value: string | number | string[];
}

export interface ConditionGroup {
  logical_operator: "AND" | "OR";
  conditions: Condition[];
}

export interface Segment {
  name: string;
  description: string;
  condition_groups: ConditionGroup[];
  estimated_scope?: string;
}

export interface TemplateSection {
  id: string;
  type: string;
  content: string;
  styles?: Record<string, string>;
}

export interface EmailTemplate {
  html: string;
  css: string;
  subject: string;
  preview_text: string;
  sections: TemplateSection[];
  version: number;
}

export interface Campaign {
  name: string;
  segment_id: string | null;
  template_id: string | null;
  subject: string;
  send_time: string | null;
  status: string;
}

export interface CustomProperty {
  name: string;
  description: string;
  javascript_code: string;
  property_type: string;
  example_value: string | null;
}

export interface ThreadSummary {
  id: string;
  agent_type: string;
  message_count: number;
  first_message: string;
  created_at: string;
  updated_at: string;
}

export interface ThreadMessage {
  role: string;
  content: string;
}

export interface ThreadData {
  messages: ThreadMessage[];
  events: Record<string, unknown>[];
  state: Record<string, unknown>;
  agent_type: string;
  created_at: string;
  updated_at: string;
}
