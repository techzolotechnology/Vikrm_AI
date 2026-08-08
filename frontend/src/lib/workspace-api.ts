import { apiClient } from "@/lib/api-client";

export interface ProjectTemplate {
  id: string;
  name: string;
  category: string;
  framework: string;
  description: string;
  icon: string;
  file_count: number;
}

export interface ProjectFile {
  id: number;
  path: string;
  content: string;
  language: string;
  updated_at?: string;
}

export interface Project {
  id: number;
  title: string;
  description: string | null;
  template: string;
  framework: string | null;
  status: string;
  files: ProjectFile[];
  updated_at?: string;
}

export interface ModelRouteResponse {
  provider: string;
  model: string;
  reason: string;
}

export interface BuildStepResult {
  step: string;
  status: "passed" | "failed" | "skipped";
  logs: string;
}

export const workspaceApi = {
  getTemplates: async (): Promise<ProjectTemplate[]> => {
    const res = await apiClient.get("/projects/templates");
    return res.data;
  },

  getProjects: async (): Promise<Project[]> => {
    const res = await apiClient.get("/projects");
    return res.data;
  },

  createProject: async (data: {
    title: string;
    description?: string;
    template: string;
    custom_prompt?: string;
  }): Promise<Project> => {
    const res = await apiClient.post("/projects", data);
    return res.data;
  },

  getProject: async (id: number): Promise<Project> => {
    const res = await apiClient.get(`/projects/${id}`);
    return res.data;
  },

  saveFile: async (projectId: number, file: { path: string; content: string; language?: string }): Promise<ProjectFile> => {
    const res = await apiClient.post(`/projects/${projectId}/files`, file);
    return res.data;
  },

  deleteFile: async (projectId: number, fileId: number): Promise<void> => {
    await apiClient.delete(`/projects/${projectId}/files/${fileId}`);
  },

  downloadZip: (projectId: number): string => {
    return `${apiClient.defaults.baseURL}/projects/${projectId}/download`;
  },

  runBuildLoop: async (projectId: number): Promise<{ steps: BuildStepResult[] }> => {
    const res = await apiClient.post(`/projects/${projectId}/build-loop`);
    return res.data;
  },

  executeTerminal: async (command: string, cwd = "."): Promise<{ stdout: string; stderr: string; exit_code: number }> => {
    const res = await apiClient.post("/terminal/execute", { command, cwd });
    return res.data;
  },

  routeModel: async (task: string, intent?: string, manualProvider?: string, manualModel?: string): Promise<ModelRouteResponse> => {
    const res = await apiClient.post("/providers/route", {
      task,
      intent,
      manual_provider: manualProvider,
      manual_model: manualModel,
    });
    return res.data;
  },

  getModels: async (): Promise<{ providers: Record<string, string[]>; ollama_online: boolean }> => {
    const res = await apiClient.get("/providers/models");
    return {
      providers: res.data.providers || { ollama: ["qwen3:8b"] },
      ollama_online: res.data.ollama_online ?? true,
    };
  },

  searchHfModels: async (q: string) => {
    const res = await apiClient.get(`/huggingface/models?q=${encodeURIComponent(q)}`);
    return res.data.models;
  },

  searchHfDatasets: async (q: string) => {
    const res = await apiClient.get(`/huggingface/datasets?q=${encodeURIComponent(q)}`);
    return res.data.datasets;
  },

  renameFile: async (projectId: number, oldPath: string, newPath: string): Promise<void> => {
    await apiClient.patch(`/projects/${projectId}/files/rename`, { old_path: oldPath, new_path: newPath });
  },

  moveFile: async (projectId: number, oldPath: string, targetFolder: string): Promise<void> => {
    await apiClient.patch(`/projects/${projectId}/files/move`, { old_path: oldPath, target_folder: targetFolder });
  },

  createFolder: async (projectId: number, folderPath: string): Promise<void> => {
    await apiClient.post(`/projects/${projectId}/folders`, { folder_path: folderPath });
  },

  triggerDeploy: async (projectId: number, target: string): Promise<{ url: string; status: string; logs: string }> => {
    const res = await apiClient.post("/deployments", { project_id: projectId, target });
    return res.data;
  },

  connectGithub: async (token: string, username?: string) => {
    const res = await apiClient.post("/github/connect", { access_token: token, username });
    return res.data;
  },

  getGithubRepos: async () => {
    const res = await apiClient.get("/github/repos");
    return res.data.repos;
  },

  generateWorkflow: async (prompt: string) => {
    const res = await apiClient.post("/workflows/generate", { prompt });
    return res.data;
  },

  // Phase 7 — Git Integration
  gitStatus: async (projectId: number) => {
    const res = await apiClient.get(`/git/status/${projectId}`);
    return res.data;
  },

  gitCommit: async (projectId: number, message: string, branch = "main") => {
    const res = await apiClient.post("/git/commit", { project_id: projectId, message, branch });
    return res.data;
  },

  gitHistory: async (projectId: number) => {
    const res = await apiClient.get(`/git/history/${projectId}`);
    return res.data;
  },

  gitBranches: async (projectId: number) => {
    const res = await apiClient.get(`/git/branches/${projectId}`);
    return res.data;
  },

  gitCheckout: async (projectId: number, branch: string) => {
    const res = await apiClient.post("/git/checkout", { project_id: projectId, branch });
    return res.data;
  },

  gitMerge: async (projectId: number, sourceBranch: string, targetBranch = "main") => {
    const res = await apiClient.post("/git/merge", { project_id: projectId, source_branch: sourceBranch, target_branch: targetBranch });
    return res.data;
  },
};
