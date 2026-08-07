import { AxiosRequestConfig } from "axios";
import { apiClient } from "@/lib/api-client";

export const api = {
  get: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const res = await apiClient.get<T>(url, config);
    return res.data;
  },
  post: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const res = await apiClient.post<T>(url, data, config);
    return res.data;
  },
  patch: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const res = await apiClient.patch<T>(url, data, config);
    return res.data;
  },
  put: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const res = await apiClient.put<T>(url, data, config);
    return res.data;
  },
  delete: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const res = await apiClient.delete<T>(url, config);
    return res.data;
  },
};

export { apiClient };
export default api;
