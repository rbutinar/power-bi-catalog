import { useState, useEffect } from 'react';
import { ApiService, SearchResults, Workspace, Dataset, Table } from '../services/api';
import DatasetDetail from './DatasetDetail';
import ScanManager from './ScanManager';
import './DataCatalog.css';

interface DataCatalogProps {
  isConfigured: boolean;
}

const DataCatalog: React.FC<DataCatalogProps> = ({ isConfigured }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('');
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [datasetTables, setDatasetTables] = useState<Table[]>([]);
  const [showTables, setShowTables] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'catalog' | 'dataset-detail'>('catalog');
  const [detailDatasetId, setDetailDatasetId] = useState<string>('');
  const [showScanManager, setShowScanManager] = useState(false);
  const [selectedScanId, setSelectedScanId] = useState<string>('');

  useEffect(() => {
    if (isConfigured) {
      loadInitialData();
    }
  }, [isConfigured, selectedScanId]);

  const loadInitialData = async () => {
    setDataLoading(true);
    try {
      const [workspacesData, datasetsData] = await Promise.all([
        ApiService.getWorkspaces(100),
        selectedScanId ? 
          ApiService.getDatasetsFromScan(selectedScanId, undefined, 100) :
          ApiService.getDatasets(undefined, 100)
      ]);
      setWorkspaces(workspacesData);
      setDatasets(datasetsData);
    } catch (error) {
      console.error('Failed to load catalog data:', error);
    } finally {
      setDataLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    setSearchLoading(true);
    try {
      const results = await ApiService.search(
        searchQuery,
        activeFilter === 'all' ? undefined : activeFilter
      );
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleWorkspaceSelect = async (workspaceId: string) => {
    setSelectedWorkspace(workspaceId);
    setSelectedDataset('');
    setDatasetTables([]);
    setShowTables(false);
    
    try {
      const workspaceDatasets = selectedScanId ?
        await ApiService.getDatasetsFromScan(selectedScanId, workspaceId, 100) :
        await ApiService.getDatasets(workspaceId, 100);
      setDatasets(workspaceDatasets);
    } catch (error) {
      console.error('Failed to load workspace datasets:', error);
    }
  };

  const handleDatasetSelect = async (datasetId: string) => {
    setSelectedDataset(datasetId);
    setShowTables(true);
    
    try {
      const tables = await ApiService.getDatasetTables(datasetId);
      setDatasetTables(tables);
    } catch (error) {
      console.error('Failed to load dataset tables:', error);
    }
  };

  const handleDatasetDetail = (datasetId: string) => {
    setDetailDatasetId(datasetId);
    setViewMode('dataset-detail');
  };

  const handleBackToCatalog = () => {
    setViewMode('catalog');
    setDetailDatasetId('');
  };

  const handleSearchItemClick = (item: any, type: string) => {
    // Handle navigation based on item type
    if (type === 'datasets') {
      // Navigate directly to dataset details
      handleDatasetDetail(item.id);
    } else if (type === 'workspaces') {
      // Navigate to workspace and clear search
      setSearchResults(null);
      setSearchQuery('');
      handleWorkspaceSelect(item.id);
    } else if (type === 'tables') {
      // Find the dataset this table belongs to and navigate there
      const dataset = datasets.find(d => d.name === item.dataset_name);
      if (dataset) {
        handleDatasetDetail(dataset.id);
      }
    } else if (type === 'columns' || type === 'measures') {
      // For columns and measures, try to find the parent dataset
      const dataset = datasets.find(d => d.name === item.dataset_name || d.name === item.table_name);
      if (dataset) {
        handleDatasetDetail(dataset.id);
      }
    }
  };

  const handleScanSelected = (scanId: string) => {
    setSelectedScanId(scanId);
    setShowScanManager(false);
    // Clear current filters and reload data from selected scan
    setSelectedWorkspace('');
    setSelectedDataset('');
    setDatasetTables([]);
    setShowTables(false);
    setSearchQuery('');
    setSearchResults(null);
    // Trigger reload with new scan
    setTimeout(() => loadInitialData(), 100);
  };

  const clearFilters = () => {
    setSelectedWorkspace('');
    setSelectedDataset('');
    setDatasetTables([]);
    setShowTables(false);
    setSearchQuery('');
    setSearchResults(null);
    loadInitialData();
  };

  if (!isConfigured) {
    return (
      <div className="catalog-container">
        <div className="catalog-message">
          <h3>Configuration Required</h3>
          <p>Please configure your Power BI tenant credentials first.</p>
        </div>
      </div>
    );
  }

  if (viewMode === 'dataset-detail') {
    return <DatasetDetail datasetId={detailDatasetId} onBack={handleBackToCatalog} />;
  }

  return (
    <div className="catalog-container">
      <div className="catalog-header">
        <div className="header-content">
          <div className="header-text">
            <h1>Data Catalog</h1>
            <p>Browse and discover your Power BI assets</p>
          </div>
          <div className="header-actions">
            <button 
              onClick={() => setShowScanManager(true)} 
              className="scan-manager-button"
            >
              📊 Manage Scans
            </button>
            {selectedScanId && (
              <div className="selected-scan-info">
                <span className="scan-indicator">📊 Using scan data</span>
                <button 
                  onClick={() => setSelectedScanId('')} 
                  className="clear-scan-button"
                  title="Switch back to default data"
                >
                  ×
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="catalog-search">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search workspaces, datasets, tables, columns, or measures..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="search-input"
          />
          <button onClick={handleSearch} className="search-button" disabled={searchLoading}>
            {searchLoading ? '⏳' : '🔍'}
          </button>
        </div>

        <div className="search-filters">
          {['all', 'workspace', 'dataset', 'table', 'column', 'measure'].map(filter => (
            <button
              key={filter}
              className={`filter-button ${activeFilter === filter ? 'active' : ''}`}
              onClick={() => setActiveFilter(filter)}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
              {filter === 'all' ? 's' : filter === 'workspace' ? 's' : ''}
            </button>
          ))}
        </div>
      </div>

      {searchResults && (
        <div className="search-results">
          <div className="results-header">
            <h3>Search Results for "{searchQuery}"</h3>
            <button onClick={() => { setSearchQuery(''); setSearchResults(null); }} className="clear-search">
              Clear Search
            </button>
          </div>
          
          {Object.entries(searchResults).map(([type, items]) => 
            items.length > 0 && (
              <div key={type} className="result-section">
                <h4>{type.charAt(0).toUpperCase() + type.slice(1)} ({items.length})</h4>
                <div className="result-grid">
                  {items.map((item: any) => (
                    <div 
                      key={item.id} 
                      className="result-item clickable"
                      onClick={() => handleSearchItemClick(item, type)}
                      title={`Click to view ${type === 'datasets' ? 'dataset details' : type === 'workspaces' ? 'workspace contents' : 'related dataset'}`}
                    >
                      <strong>{item.name}</strong>
                      {item.workspace_name && <div className="item-meta">in {item.workspace_name}</div>}
                      {item.dataset_name && <div className="item-meta">in {item.dataset_name}</div>}
                      {item.table_name && <div className="item-meta">in {item.table_name}</div>}
                      {item.data_type && <div className="item-meta">Type: {item.data_type}</div>}
                      {item.type && <div className="item-meta">Type: {item.type}</div>}
                      <div className="click-hint">Click to navigate →</div>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}
        </div>
      )}

      <div className="catalog-content">
        <div className="catalog-sidebar">
          <div className="filter-section">
            <div className="filter-header">
              <h3>Browse by Workspace</h3>
              {(selectedWorkspace || selectedDataset) && (
                <button onClick={clearFilters} className="clear-filters">Clear Filters</button>
              )}
            </div>
            
            {dataLoading ? (
              <div className="loading">Loading workspaces...</div>
            ) : (
              <div className="workspace-list">
                {workspaces.slice(0, 20).map(workspace => (
                  <div
                    key={workspace.id}
                    className={`workspace-item ${selectedWorkspace === workspace.id ? 'selected' : ''}`}
                    onClick={() => handleWorkspaceSelect(workspace.id)}
                  >
                    <div className="workspace-name">{workspace.name}</div>
                    <div className="workspace-meta">
                      {workspace.datasets_count} datasets
                      {workspace.is_on_dedicated_capacity && <span className="premium-badge">Premium</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="catalog-main">
          <div className="catalog-grid">
            {selectedWorkspace ? (
              <>
                <div className="section-header">
                  <h3>Datasets in {workspaces.find(w => w.id === selectedWorkspace)?.name}</h3>
                  <span className="item-count">{datasets.length} datasets</span>
                </div>
                
                <div className="items-grid">
                  {datasets.map(dataset => (
                    <div
                      key={dataset.id}
                      className={`catalog-item dataset-item ${selectedDataset === dataset.id ? 'selected' : ''}`}
                      onClick={() => handleDatasetDetail(dataset.id)}
                    >
                      <div className="item-header">
                        <h4>{dataset.name}</h4>
                        <div className="item-type">Dataset</div>
                      </div>
                      <div className="item-details">
                        <div className="detail-row">
                          <span>Tables: {dataset.tables_count}</span>
                          <span>Measures: {dataset.measures_count}</span>
                        </div>
                        {dataset.modified_date && (
                          <div className="detail-row">
                            <span>Modified: {new Date(dataset.modified_date).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {showTables && datasetTables.length > 0 && (
                  <>
                    <div className="section-header">
                      <h3>Tables in {datasets.find(d => d.id === selectedDataset)?.name}</h3>
                      <span className="item-count">{datasetTables.length} tables</span>
                    </div>
                    
                    <div className="items-grid">
                      {datasetTables.map(table => (
                        <div key={table.id} className="catalog-item table-item">
                          <div className="item-header">
                            <h4>{table.name}</h4>
                            <div className="item-type">Table</div>
                          </div>
                          <div className="item-details">
                            <div className="detail-row">
                              <span>Columns: {table.columns_count}</span>
                              {table.row_count && <span>Rows: {table.row_count?.toLocaleString()}</span>}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </>
            ) : (
              <>
                <div className="section-header">
                  <h3>All Workspaces</h3>
                  <span className="item-count">{workspaces.length} workspaces</span>
                </div>
                
                <div className="items-grid">
                  {workspaces.map(workspace => (
                    <div
                      key={workspace.id}
                      className="catalog-item workspace-item-card"
                      onClick={() => handleWorkspaceSelect(workspace.id)}
                    >
                      <div className="item-header">
                        <h4>{workspace.name}</h4>
                        <div className="item-type">
                          Workspace
                          {workspace.is_on_dedicated_capacity && <span className="premium-badge">Premium</span>}
                        </div>
                      </div>
                      <div className="item-details">
                        <div className="detail-row">
                          <span>Datasets: {workspace.datasets_count}</span>
                          <span>Type: {workspace.type || 'Standard'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {showScanManager && (
        <ScanManager 
          onClose={() => setShowScanManager(false)}
          onScanSelected={handleScanSelected}
        />
      )}
    </div>
  );
};

export default DataCatalog;