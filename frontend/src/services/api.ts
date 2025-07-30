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

export interface DatasetDetails {
  id: string;
  name: string;
  workspace_id: string;
  workspace_name: string;
  created_date?: string;
  modified_date?: string;
  is_on_dedicated_capacity?: boolean;
  tables: Array<{
    id: string;
    name: string;
    row_count?: number;
    columns_count: number;
  }>;
  measures: Array<{
    id: string;
    name: string;
    expression?: string;
    description?: string;
    is_hidden: boolean;
  }>;
  relationships: Array<{
    id: string;
    from_table: string;
    from_column: string;
    to_table: string;
    to_column: string;
    cross_filtering_behavior?: string;
    is_active?: boolean;
  }>;
  summary: {
    total_tables: number;
    total_measures: number;
    total_relationships: number;
    total_columns: number;
    total_rows: number;
  };
}

export interface Column {
  id: string;
  name: string;
  data_type?: string;
  description?: string;
  is_hidden?: boolean;
  data_category?: string;
  is_key?: boolean;
  table_name: string;
}

// Scan-related interfaces
export interface ScanRequest {
  scan_name?: string;
  description?: string;
  workspace_filter?: string;
  workspace_id_filter?: string;
  dataset_filter?: string;
  dataset_id_filter?: string;
}

export interface ScanResponse {
  scan_id: string;
  scan_name: string;
  description: string;
  status: string;
  progress: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
  total_workspaces: number;
  processed_workspaces: number;
  total_datasets: number;
  processed_datasets: number;
}

export interface ScanListResponse {
  scans: ScanResponse[];
}

export class ApiService {
  private static async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    console.log('Making API request to:', url);
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      console.log('Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
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

  static async getDatasetDetails(datasetId: string): Promise<DatasetDetails> {
    console.log('Requesting dataset details for ID:', datasetId);
    console.log('Full URL will be:', `${API_BASE_URL}/api/datasets/${datasetId}/details`);
    return this.request<DatasetDetails>(`/api/datasets/${datasetId}/details`);
  }

  static async getTableColumns(tableId: string): Promise<Column[]> {
    return this.request<Column[]>(`/api/tables/${tableId}/columns`);
  }

  // Debug method to test API connectivity
  static async testConnection(): Promise<any> {
    console.log('Testing API connection...');
    return this.request<any>('/api/test');
  }

  // Test dataset details endpoint
  static async testDatasetDetails(): Promise<any> {
    console.log('Testing dataset details endpoint...');
    return this.request<any>('/api/datasets/test-id/details');
  }

  // Scanning API methods
  static async createScan(scanRequest: ScanRequest): Promise<ScanResponse> {
    return this.request<ScanResponse>('/api/scans', {
      method: 'POST',
      body: JSON.stringify(scanRequest),
    });
  }

  static async listScans(): Promise<ScanListResponse> {
    return this.request<ScanListResponse>('/api/scans');
  }

  static async getScan(scanId: string): Promise<ScanResponse> {
    return this.request<ScanResponse>(`/api/scans/${scanId}`);
  }

  static async deleteScan(scanId: string): Promise<{ message: string }> {
    return this.request(`/api/scans/${scanId}`, {
      method: 'DELETE',
    });
  }

  static async cancelScan(scanId: string): Promise<{ message: string }> {
    return this.request(`/api/scans/${scanId}/cancel`, {
      method: 'POST',
    });
  }

  // Updated methods to support scan selection
  static async getDatasetsFromScan(scanId?: string, workspaceId?: string, limit: number = 100): Promise<Dataset[]> {
    const query = new URLSearchParams({ limit: limit.toString() });
    if (workspaceId) {
      query.append('workspace_id', workspaceId);
    }
    if (scanId) {
      query.append('scan_id', scanId);
    }
    return this.request<Dataset[]>(`/api/datasets/list?${query.toString()}`);
  }
}