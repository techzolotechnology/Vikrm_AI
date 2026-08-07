/**
 * Project Artifact Parser for Vikrm AI Platform.
 * Parses markdown response streams containing file headers (### path/to/file.ext)
 * into a structured ProjectArtifact object.
 */

export interface ParsedFile {
  path: string;
  language: string;
  content: string;
}

export interface ProjectArtifact {
  title: string;
  framework: string;
  files: ParsedFile[];
  summaryText: string;
  isProject: boolean;
}

export function parseProjectArtifact(text: string): ProjectArtifact {
  if (!text) {
    return { title: "", framework: "React", files: [], summaryText: "", isProject: false };
  }

  // 1. Primary: Regex to match ### path/to/file.ext followed by ```lang\ncode\n```
  const fileBlockRegex = /###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```/g;
  const markdownFiles: ParsedFile[] = [];
  let match;

  while ((match = fileBlockRegex.exec(text)) !== null) {
    const rawPath = match[1].trim();
    const cleanPath = rawPath.replace(/^`+|`+$/g, "").replace(/^\.\//, "");
    const language = (match[2] || "typescript").trim();
    const content = match[3].trim();

    markdownFiles.push({
      path: cleanPath,
      language: language.toLowerCase(),
      content,
    });
  }

  if (markdownFiles.length > 0) {
    const isProject = markdownFiles.length >= 2 || (markdownFiles.length === 1 && markdownFiles[0].path.includes("/"));
    let summaryText = text.replace(fileBlockRegex, "").trim();
    if (!summaryText) {
      summaryText = `Generated a complete ${markdownFiles.length}-file application workspace.`;
    }

    let title = "Generated Project";
    let framework = "React";
    const appFile = markdownFiles.find((f) => f.path.includes("App.") || f.path.includes("index."));
    if (appFile) {
      if (appFile.path.endsWith(".tsx") || appFile.path.endsWith(".jsx")) framework = "React";
      else if (appFile.path.endsWith(".py")) framework = "FastAPI / Python";
      else if (appFile.path.endsWith(".html")) framework = "HTML/JS";
    }

    return {
      title,
      framework,
      files: markdownFiles,
      summaryText,
      isProject,
    };
  }

  // 2. Fallback: JSON Schema Parsing ({ "project": { "name": "...", "files": [...] } })
  try {
    const jsonMatch = text.match(/\{[\s\S]*"project"[\s\S]*\}/);
    if (jsonMatch) {
      const parsedObj = JSON.parse(jsonMatch[0]);
      const proj = parsedObj.project || parsedObj;
      if (proj && Array.isArray(proj.files) && proj.files.length > 0) {
        const jsonFiles: ParsedFile[] = proj.files.map((f: any) => ({
          path: (f.path || f.filename || "file.txt").replace(/^`+|`+$/g, "").replace(/^\.\//, ""),
          language: (f.language || f.lang || "typescript").toLowerCase(),
          content: f.content || "",
        }));

        return {
          title: proj.name || proj.title || "Generated Production Project",
          framework: Array.isArray(proj.techStack) ? proj.techStack.join(" + ") : (proj.framework || "React"),
          files: jsonFiles,
          summaryText: proj.description || `Generated complete ${jsonFiles.length}-file production application.`,
          isProject: true,
        };
      }
    }
  } catch (e) {
    // Ignore JSON parse errors
  }

  return {
    title: "Generated Project",
    framework: "React",
    files: [],
    summaryText: text,
    isProject: false,
  };
}
