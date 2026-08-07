/**
 * Utility to format message content safely, preventing '[object Object]' rendering
 * and expanding structured LLM JSON outputs into clean GitHub-Flavored Markdown file blocks.
 */

export function formatMessageContent(rawContent: any): string {
  if (rawContent === null || rawContent === undefined) {
    return "";
  }

  let contentStr: string = "";

  // 1. Convert non-string objects to JSON strings safely
  if (typeof rawContent === "object") {
    console.error("BAD OBJECT DETECTED in formatMessageContent", {
      value: rawContent,
      typeof: typeof rawContent,
      constructor: rawContent?.constructor?.name,
      stack: new Error().stack,
    });
    try {
      contentStr = JSON.stringify(rawContent);
    } catch {
      contentStr = String(rawContent);
    }
  } else {
    contentStr = String(rawContent);
  }

  // 2. Prevent literal '[object Object]' strings
  if (contentStr.trim() === "[object Object]") {
    console.error("BAD OBJECT DETECTED (Literal '[object Object]') in formatMessageContent", {
      value: rawContent,
      typeof: typeof rawContent,
      constructor: rawContent?.constructor?.name,
      stack: new Error().stack,
    });
    try {
      contentStr = JSON.stringify(rawContent, null, 2);
    } catch {
      contentStr = "Invalid provider response";
    }
    if (contentStr === "[object Object]" || !contentStr) {
      contentStr = "Invalid provider response";
    }
  }

  const trimmed = contentStr.trim();
  let parsedObj: any = null;

  // 3. Try parsing JSON if rawContent was an object or string contains JSON
  if (typeof rawContent === "object") {
    parsedObj = rawContent;
  } else if (
    (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
    (trimmed.startsWith("[") && trimmed.endsWith("]"))
  ) {
    try {
      parsedObj = JSON.parse(trimmed);
    } catch {
      parsedObj = null;
    }
  }

  // 4. Handle structured JSON payload containing 'files' array
  if (parsedObj && typeof parsedObj === "object") {
    if (Array.isArray(parsedObj.files) && parsedObj.files.length > 0) {
      const fileBlocks = parsedObj.files
        .map((file: any) => {
          const filePath = file.path || file.filename || file.name || "file";
          const fileContent =
            typeof file.content === "string"
              ? file.content
              : typeof file.code === "string"
              ? file.code
              : JSON.stringify(file.content || file.code || "", null, 2);

          // Infer extension for markdown syntax highlighting
          const ext = filePath.split(".").pop()?.toLowerCase() || "";
          const langMap: Record<string, string> = {
            tsx: "tsx",
            ts: "typescript",
            js: "javascript",
            jsx: "jsx",
            py: "python",
            sh: "bash",
            bash: "bash",
            json: "json",
            yaml: "yaml",
            yml: "yaml",
            md: "markdown",
            html: "html",
            css: "css",
            sql: "sql",
            dockerfile: "dockerfile",
          };
          const lang = langMap[ext] || ext || "code";

          return `### ${filePath}\n\n\`\`\`${lang}\n${fileContent}\n\`\`\``;
        })
        .join("\n\n");

      return fileBlocks;
    }

    // Extract common message/text/response properties if present
    if (typeof parsedObj.message === "string") return parsedObj.message;
    if (typeof parsedObj.text === "string") return parsedObj.text;
    if (typeof parsedObj.content === "string") return parsedObj.content;
    if (typeof parsedObj.response === "string") return parsedObj.response;
    if (typeof parsedObj.delta === "string") return parsedObj.delta;

    // Fallback for generic objects: render as formatted json block
    return `\`\`\`json\n${JSON.stringify(parsedObj, null, 2)}\n\`\`\``;
  }

  return contentStr;
}
