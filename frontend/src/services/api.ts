const API_BASE_URL = 'http://localhost:8000';

export interface TenantConfig {
  tenant_id: string;
  client_id: string;
  client_secret: string;
}

export interface TenantConfigResponse {
  tenant_id?: string;
  client_id?: string;
  has_client_secret: boolean;
  is_configured: boolean;
}

export class ApiService {
  private static async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  static async getConfig(): Promise<TenantConfigResponse> {
    return this.request<TenantConfigResponse>('/api/config');
  }

  static async updateConfig(config: TenantConfig): Promise<{ message: string; is_configured: boolean }> {
    return this.request('/api/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  static async getWorkspaces(): Promise<{ workspaces: any[]; message?: string }> {
    return this.request('/api/workspaces');
  }

  static async getDatasets(): Promise<{ datasets: any[]; message?: string }> {
    return this.request('/api/datasets');
  }

  static async healthCheck(): Promise<{ message: string; status: string }> {
    return this.request('/');
  }
}