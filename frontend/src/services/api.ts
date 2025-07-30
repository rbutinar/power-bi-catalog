const API_BASE_URL = 'http://localhost:8001';

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

export interface AnalysisStats {
  latest_run_date?: string;
  total_workspaces: number;
  total_datasets: number;
  total_tables: number;
  total_columns: number;
  total_measures: number;
  total_relationships: number;
  workspaces_on_dedicated: number;
}

export interface Workspace {
  id: string;
  name: string;
  type?: string;
  is_on_dedicated_capacity?: boolean;
  datasets_count?: number;
}

export interface Dataset {
  id: string;
  name: string;
  workspace_id: string;
  workspace_name?: string;
  created_date?: string;
  modified_date?: string;
  tables_count?: number;
  measures_count?: number;
}

export interface Table {
  id: string;
  name: string;
  dataset_id: string;
  dataset_name?: string;
  row_count?: number;
  columns_count?: number;
}

export interface SearchResults {
  workspaces: Array<{id: string, name: string, type: string}>;
  datasets: Array<{id: string, name: string, workspace_name: string}>;
  tables: Array<{id: string, name: string, dataset_name: string}>;
  columns: Array<{id: string, name: string, table_name: string, data_type: string}>;
  measures: Array<{id: string, name: string, dataset_name: string}>;
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

  // Legacy endpoints - keeping for backward compatibility
  static async getWorkspacesLegacy(): Promise<{ workspaces: any[]; message?: string }> {
    return this.request('/api/workspaces');
  }

  static async getDatasetsLegacy(): Promise<{ datasets: any[]; message?: string }> {
    return this.request('/api/datasets');
  }

  static async healthCheck(): Promise<{ message: string; status: string }> {
    return this.request('/');
  }

  static async getStats(): Promise<AnalysisStats> {
    return this.request<AnalysisStats>('/api/stats');
  }

  static async getWorkspaces(limit: number = 100): Promise<Workspace[]> {
    return this.request<Workspace[]>(`/api/workspaces/list?limit=${limit}`);
  }

  static async getDatasets(workspaceId?: string, limit: number = 100): Promise<Dataset[]> {
    const query = new URLSearchParams({ limit: limit.toString() });
    if (workspaceId) {
      query.append('workspace_id', workspaceId);
    }
    return this.request<Dataset[]>(`/api/datasets/list?${query.toString()}`);
  }

  static async getDatasetTables(datasetId: string): Promise<Table[]> {
    return this.request<Table[]>(`/api/datasets/${datasetId}/tables`);
  }

  static async search(query: string, type?: string): Promise<SearchResults> {
    const searchParams = new URLSearchParams({ q: query });
    if (type) {
      searchParams.append('type', type);
    }
    return this.request<SearchResults>(`/api/search?${searchParams.toString()}`);
  }
}