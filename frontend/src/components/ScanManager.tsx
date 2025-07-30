import { useState, useEffect } from 'react';
import { ApiService, ScanResponse, ScanRequest } from '../services/api';
import './ScanManager.css';

interface ScanManagerProps {
  onClose: () => void;
  onScanSelected?: (scanId: string) => void;
}

const ScanManager: React.FC<ScanManagerProps> = ({ onClose, onScanSelected }) => {
  const [scans, setScans] = useState<ScanResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewScanForm, setShowNewScanForm] = useState(false);
  const [newScanRequest, setNewScanRequest] = useState<ScanRequest>({});
  const [creatingScan, setCreatingScan] = useState(false);

  useEffect(() => {
    loadScans();
    // Set up polling for scan status updates
    const interval = setInterval(loadScans, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadScans = async () => {
    try {
      const response = await ApiService.listScans();
      setScans(response.scans);
      setError(null);
    } catch (err: any) {
      setError(`Failed to load scans: ${err.message}`);
      console.error('Failed to load scans:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateScan = async () => {
    if (!newScanRequest.scan_name?.trim()) {
      setError('Scan name is required');
      return;
    }

    setCreatingScan(true);
    setError(null);

    try {
      const response = await ApiService.createScan(newScanRequest);
      setScans(prev => [response, ...prev]);
      setShowNewScanForm(false);
      setNewScanRequest({});
    } catch (err: any) {
      setError(`Failed to create scan: ${err.message}`);
    } finally {
      setCreatingScan(false);
    }
  };

  const handleDeleteScan = async (scanId: string) => {
    if (!confirm('Are you sure you want to delete this scan? This action cannot be undone.')) {
      return;
    }

    try {
      await ApiService.deleteScan(scanId);
      setScans(prev => prev.filter(scan => scan.scan_id !== scanId));
    } catch (err: any) {
      setError(`Failed to delete scan: ${err.message}`);
    }
  };

  const handleCancelScan = async (scanId: string) => {
    try {
      await ApiService.cancelScan(scanId);
      await loadScans(); // Refresh to get updated status
    } catch (err: any) {
      setError(`Failed to cancel scan: ${err.message}`);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return '#4caf50';
      case 'running': case 'processing': return '#2196f3';
      case 'pending': return '#ff9800';
      case 'failed': return '#f44336';
      case 'cancelled': return '#757575';
      default: return '#666';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return '✅';
      case 'running': case 'processing': return '🔄';
      case 'pending': return '⏳';
      case 'failed': return '❌';
      case 'cancelled': return '⏹️';
      default: return '❓';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="scan-manager-overlay">
        <div className="scan-manager">
          <div className="scan-manager-header">
            <h2>Scan Manager</h2>
            <button onClick={onClose} className="close-button">×</button>
          </div>
          <div className="loading">Loading scans...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="scan-manager-overlay">
      <div className="scan-manager">
        <div className="scan-manager-header">
          <h2>Scan Manager</h2>
          <div className="header-actions">
            <button 
              onClick={() => setShowNewScanForm(true)} 
              className="new-scan-button"
              disabled={creatingScan}
            >
              + New Scan
            </button>
            <button onClick={onClose} className="close-button">×</button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)} className="dismiss-error">×</button>
          </div>
        )}

        {showNewScanForm && (
          <div className="new-scan-form">
            <h3>Create New Scan</h3>
            <div className="form-group">
              <label>Scan Name *</label>
              <input
                type="text"
                value={newScanRequest.scan_name || ''}
                onChange={(e) => setNewScanRequest(prev => ({ ...prev, scan_name: e.target.value }))}
                placeholder="e.g., Weekly-Baseline-2025-01-30"
                disabled={creatingScan}
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newScanRequest.description || ''}
                onChange={(e) => setNewScanRequest(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Optional description for this scan..."
                disabled={creatingScan}
              />
            </div>
            <div className="form-group">
              <label>Workspace Filter (optional)</label>
              <input
                type="text"
                value={newScanRequest.workspace_filter || ''}
                onChange={(e) => setNewScanRequest(prev => ({ ...prev, workspace_filter: e.target.value }))}
                placeholder="Filter workspaces containing this text"
                disabled={creatingScan}
              />
            </div>
            <div className="form-actions">
              <button 
                onClick={handleCreateScan} 
                className="create-button"
                disabled={creatingScan}
              >
                {creatingScan ? 'Creating...' : 'Create & Start Scan'}
              </button>
              <button 
                onClick={() => {
                  setShowNewScanForm(false);
                  setNewScanRequest({});
                  setError(null);
                }} 
                className="cancel-button"
                disabled={creatingScan}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="scans-list">
          <h3>Available Scans ({scans.length})</h3>
          {scans.length === 0 ? (
            <div className="no-scans">
              <p>No scans available. Create your first scan to get started!</p>
            </div>
          ) : (
            <div className="scans-grid">
              {scans.map(scan => (
                <div key={scan.scan_id} className="scan-card">
                  <div className="scan-header">
                    <div className="scan-name">
                      <span className="status-icon">{getStatusIcon(scan.status)}</span>
                      {scan.scan_name}
                    </div>
                    <div className="scan-actions">
                      {scan.status === 'completed' && onScanSelected && (
                        <button 
                          onClick={() => onScanSelected(scan.scan_id)}
                          className="select-button"
                          title="Use this scan data"
                        >
                          Use
                        </button>
                      )}
                      {(scan.status === 'running' || scan.status === 'pending') && (
                        <button 
                          onClick={() => handleCancelScan(scan.scan_id)}
                          className="cancel-scan-button"
                          title="Cancel scan"
                        >
                          Cancel
                        </button>
                      )}
                      <button 
                        onClick={() => handleDeleteScan(scan.scan_id)}
                        className="delete-button"
                        title="Delete scan"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  
                  <div className="scan-status">
                    <span 
                      className="status-badge" 
                      style={{ backgroundColor: getStatusColor(scan.status) }}
                    >
                      {scan.status.toUpperCase()}
                    </span>
                    {(scan.status === 'running' || scan.status === 'processing') && (
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${scan.progress}%` }}
                        ></div>
                        <span className="progress-text">{scan.progress}%</span>
                      </div>
                    )}
                  </div>

                  <div className="scan-details">
                    <div className="scan-description">{scan.description}</div>
                    <div className="scan-meta">
                      <div>Created: {formatDate(scan.created_at)}</div>
                      {scan.completed_at && (
                        <div>Completed: {formatDate(scan.completed_at)}</div>
                      )}
                      {scan.status === 'completed' && (
                        <div className="scan-stats">
                          {scan.total_workspaces} workspaces • {scan.total_datasets} datasets
                        </div>
                      )}
                    </div>
                    {scan.error_message && (
                      <div className="scan-error">
                        Error: {scan.error_message}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScanManager;