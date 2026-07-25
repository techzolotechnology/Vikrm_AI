export interface ToolInfo {
  name: string;
  description: string;
}

export interface ToolExecution {
  id: number;
  tool_name: string;
  input_text: string;
  output_text: string | null;
  status: "success" | "failed";
  error: string | null;
  duration_ms: number;
  created_at: string;
}
