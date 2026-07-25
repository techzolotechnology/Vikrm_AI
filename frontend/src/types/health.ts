export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
}

export interface ReadinessResponse {
  status: "ready" | "degraded";
  database: "up" | "down";
  redis: "up" | "down";
}

export interface VersionResponse {
  app_name: string;
  version: string;
  environment: string;
}
