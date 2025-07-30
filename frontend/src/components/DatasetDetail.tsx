import { useState, useEffect } from 'react';
import { ApiService, DatasetDetails, Column } from '../services/api';
import './DatasetDetail.css';

interface DatasetDetailProps {
  datasetId: string;
  onBack: () => void;
}

const DatasetDetail: React.FC<DatasetDetailProps> = ({ datasetId, onBack }) => {
  const [dataset, setDataset] = useState<DatasetDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'tables' | 'measures' | 'relationships'>('overview');
  const [expandedTable, setExpandedTable] = useState<string | null>(null);
  const [tableColumns, setTableColumns] = useState<Record<string, Column[]>>({});
  const [expandedMeasure, setExpandedMeasure] = useState<string | null>(null);

  useEffect(() => {
    loadDatasetDetails();
  }, [datasetId]);

  const loadDatasetDetails = async () => {
    setLoading(true);
    setError(null);
    console.log('Loading dataset details for ID:', datasetId);
    
    try {
      // First test basic connectivity
      console.log('Testing API connection...');
      await ApiService.testConnection();
      console.log('API connection successful, testing dataset details endpoint...');
      
      await ApiService.testDatasetDetails();
      console.log('Dataset details endpoint test successful, loading actual dataset...');
      
      const details = await ApiService.getDatasetDetails(datasetId);
      console.log('Dataset details loaded:', details);
      setDataset(details);
    } catch (err: any) {
      console.error('Failed to load dataset details:', err);
      setError(`Failed to load dataset details: ${err.message || err.toString()}`);
    } finally {
      setLoading(false);
    }
  };

  const loadTableColumns = async (tableId: string) => {
    if (tableColumns[tableId]) {
      return; // Already loaded
    }
    
    try {
      const columns = await ApiService.getTableColumns(tableId);
      setTableColumns(prev => ({ ...prev, [tableId]: columns }));
    } catch (err) {
      console.error('Failed to load table columns:', err);
    }
  };

  const handleTableExpand = (tableId: string) => {
    if (expandedTable === tableId) {
      setExpandedTable(null);
    } else {
      setExpandedTable(tableId);
      loadTableColumns(tableId);
    }
  };

  const handleMeasureExpand = (measureId: string) => {
    setExpandedMeasure(expandedMeasure === measureId ? null : measureId);
  };

  if (loading) {
    return (
      <div className="dataset-detail">
        <div className="detail-header">
          <button onClick={onBack} className="back-button">← Back</button>
          <div className="loading">Loading dataset details...</div>
        </div>
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="dataset-detail">
        <div className="detail-header">
          <button onClick={onBack} className="back-button">← Back</button>
          <div className="error-message">{error || 'Dataset not found'}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dataset-detail">
      <div className="detail-header">
        <button onClick={onBack} className="back-button">← Back to Catalog</button>
        <div className="dataset-info">
          <h1>{dataset.name}</h1>
          <div className="dataset-meta">
            <span>Workspace: {dataset.workspace_name}</span>
            <span>•</span>
            <span>{dataset.summary.total_tables} tables</span>
            <span>•</span>
            <span>{dataset.summary.total_measures} measures</span>
            <span>•</span>
            <span>{dataset.summary.total_columns} columns</span>
            {dataset.is_on_dedicated_capacity && <span className="premium-badge">Premium</span>}
          </div>
        </div>
      </div>

      <div className="detail-tabs">
        {(['overview', 'tables', 'measures', 'relationships'] as const).map(tab => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            <span className="tab-count">
              {tab === 'tables' && dataset.summary.total_tables}
              {tab === 'measures' && dataset.summary.total_measures}
              {tab === 'relationships' && dataset.summary.total_relationships}
            </span>
          </button>
        ))}
      </div>

      <div className="detail-content">
        {activeTab === 'overview' && (
          <div className="overview-content">
            <div className="overview-grid">
              <div className="overview-card">
                <h3>📊 Summary</h3>
                <div className="stat-grid">
                  <div className="stat-item">
                    <span className="stat-value">{dataset.summary.total_tables}</span>
                    <span className="stat-label">Tables</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value">{dataset.summary.total_columns}</span>
                    <span className="stat-label">Columns</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value">{dataset.summary.total_measures}</span>
                    <span className="stat-label">Measures</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value">{dataset.summary.total_rows.toLocaleString()}</span>
                    <span className="stat-label">Total Rows</span>
                  </div>
                </div>
              </div>

              <div className="overview-card">
                <h3>📅 Timeline</h3>
                <div className="timeline-info">
                  {dataset.created_date && (
                    <div className="timeline-item">
                      <span className="timeline-label">Created:</span>
                      <span>{new Date(dataset.created_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  {dataset.modified_date && (
                    <div className="timeline-item">
                      <span className="timeline-label">Last Modified:</span>
                      <span>{new Date(dataset.modified_date).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="overview-card">
                <h3>🏢 Workspace Info</h3>
                <div className="workspace-info">
                  <div className="info-item">
                    <span className="info-label">Name:</span>
                    <span>{dataset.workspace_name}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Premium Capacity:</span>
                    <span>{dataset.is_on_dedicated_capacity ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="quick-preview">
              <h3>🔍 Quick Preview</h3>
              <div className="preview-grid">
                <div className="preview-section">
                  <h4>Top Tables</h4>
                  <div className="preview-list">
                    {dataset.tables.slice(0, 5).map(table => (
                      <div key={table.id} className="preview-item">
                        <span className="item-name">{table.name}</span>
                        <span className="item-meta">{table.columns_count} cols, {table.row_count?.toLocaleString() || '0'} rows</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="preview-section">
                  <h4>Recent Measures</h4>
                  <div className="preview-list">
                    {dataset.measures.slice(0, 5).map(measure => (
                      <div key={measure.id} className="preview-item">
                        <span className="item-name">{measure.name}</span>
                        {measure.description && <span className="item-meta">{measure.description}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tables' && (
          <div className="tables-content">
            <div className="content-header">
              <h3>Tables ({dataset.tables.length})</h3>
              <div className="content-meta">
                Total columns: {dataset.summary.total_columns} | Total rows: {dataset.summary.total_rows.toLocaleString()}
              </div>
            </div>
            <div className="tables-list">
              {dataset.tables.map(table => (
                <div key={table.id} className="table-item">
                  <div 
                    className="table-header"
                    onClick={() => handleTableExpand(table.id)}
                  >
                    <div className="table-info">
                      <h4>{table.name}</h4>
                      <div className="table-meta">
                        {table.columns_count} columns • {table.row_count?.toLocaleString() || '0'} rows
                      </div>
                    </div>
                    <div className="expand-icon">
                      {expandedTable === table.id ? '▼' : '▶'}
                    </div>
                  </div>
                  
                  {expandedTable === table.id && (
                    <div className="table-columns">
                      <h5>Columns</h5>
                      {tableColumns[table.id] ? (
                        <>
                          {tableColumns[table.id].every(col => col.name === 'Unknown' || !col.name) && (
                            <div className="metadata-warning">
                              ⚠️ Column details are not available for this table. This may be due to:
                              <ul>
                                <li>Limited metadata permissions</li>
                                <li>Dataset type restrictions</li>
                                <li>Power BI service limitations</li>
                              </ul>
                              Found {tableColumns[table.id].length} columns with limited metadata.
                            </div>
                          )}
                          <div className="columns-grid">
                            {tableColumns[table.id].map((column, index) => (
                              <div key={column.id} className="column-item">
                                <div className="column-header">
                                  <span className="column-name">
                                    {column.name && column.name !== 'Unknown' 
                                      ? column.name 
                                      : `Column ${index + 1}`}
                                  </span>
                                  <span className="column-type">
                                    {column.data_type && column.data_type !== 'Unknown' 
                                      ? column.data_type 
                                      : 'Type not available'}
                                  </span>
                                  {column.is_key && <span className="key-badge">🔑</span>}
                                  {column.is_hidden && <span className="hidden-badge">👁️‍🗨️</span>}
                                </div>
                                {column.description && column.description !== 'Unknown' && (
                                  <div className="column-description">{column.description}</div>
                                )}
                                {column.data_category && column.data_category !== 'Unknown' && (
                                  <div className="column-category">Category: {column.data_category}</div>
                                )}
                              </div>
                            ))}
                          </div>
                        </>
                      ) : (
                        <div className="loading">Loading columns...</div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'measures' && (
          <div className="measures-content">
            <div className="content-header">
              <h3>Measures ({dataset.measures.length})</h3>
              <div className="content-meta">
                DAX formulas and calculations
              </div>
            </div>
            <div className="measures-list">
              {dataset.measures.map(measure => (
                <div key={measure.id} className="measure-item">
                  <div 
                    className="measure-header"
                    onClick={() => handleMeasureExpand(measure.id)}
                  >
                    <div className="measure-info">
                      <h4>{measure.name}</h4>
                      {measure.description && (
                        <div className="measure-description">{measure.description}</div>
                      )}
                      {measure.is_hidden && <span className="hidden-badge">Hidden</span>}
                    </div>
                    <div className="expand-icon">
                      {expandedMeasure === measure.id ? '▼' : '▶'}
                    </div>
                  </div>
                  
                  {expandedMeasure === measure.id && measure.expression && (
                    <div className="measure-expression">
                      <h5>DAX Expression</h5>
                      <pre className="dax-code">{measure.expression}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="relationships-content">
            <div className="content-header">
              <h3>Relationships ({dataset.relationships.length})</h3>
              <div className="content-meta">
                Data model connections and dependencies
              </div>
            </div>
            {dataset.relationships.length > 0 ? (
              <div className="relationships-list">
                {dataset.relationships.map(rel => (
                  <div key={rel.id} className="relationship-item">
                    <div className="relationship-diagram">
                      <div className="table-box">{rel.from_table}</div>
                      <div className="relationship-arrow">
                        <div className="column-name">{rel.from_column}</div>
                        <div className="arrow">→</div>
                        <div className="column-name">{rel.to_column}</div>
                      </div>
                      <div className="table-box">{rel.to_table}</div>
                    </div>
                    <div className="relationship-meta">
                      {rel.cross_filtering_behavior && (
                        <span className="filter-behavior">Filter: {rel.cross_filtering_behavior}</span>
                      )}
                      {rel.is_active !== undefined && (
                        <span className={`status ${rel.is_active ? 'active' : 'inactive'}`}>
                          {rel.is_active ? 'Active' : 'Inactive'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No relationships defined in this dataset.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DatasetDetail;