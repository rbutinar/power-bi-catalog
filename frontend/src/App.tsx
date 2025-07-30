import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ConfigurationForm from './components/ConfigurationForm'
import { ApiService, TenantConfigResponse, AnalysisStats, Workspace, Dataset } from './services/api'
import './App.css'

interface TenantConfig {
  tenantId: string;
  clientId: string;
  clientSecret: string;
}

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [tenantConfig, setTenantConfig] = useState<TenantConfig | null>(null)
  const [isConfigured, setIsConfigured] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [apiError, setApiError] = useState<string | null>(null)
  const [stats, setStats] = useState<AnalysisStats | null>(null)
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [dataLoading, setDataLoading] = useState(false)

  // Check configuration from backend and localStorage on app load
  useEffect(() => {
    loadConfiguration()
  }, [])

  const loadConfiguration = async () => {
    setIsLoading(true)
    setApiError(null)
    
    try {
      // First try to get config from backend (.env file)
      const backendConfig = await ApiService.getConfig()
      
      if (backendConfig.is_configured) {
        // Backend has configuration, use it
        const config: TenantConfig = {
          tenantId: backendConfig.tenant_id || '',
          clientId: backendConfig.client_id || '',
          clientSecret: backendConfig.has_client_secret ? '••••••••••••••••' : ''
        }
        setTenantConfig(config)
        setIsConfigured(true)
        setCurrentPage('dashboard')
        // Load data after setting configuration
        setTimeout(() => loadData(), 100)
      } else {
        // Try localStorage as fallback
        const savedConfig = localStorage.getItem('tenantConfig')
        if (savedConfig) {
          const config = JSON.parse(savedConfig)
          setTenantConfig(config)
          setIsConfigured(true)
          setCurrentPage('dashboard')
        } else {
          // No configuration found, show config page
          setCurrentPage('config')
        }
      }
    } catch (error) {
      console.error('Failed to load configuration:', error)
      setApiError('Failed to connect to backend. Using local configuration only.')
      
      // Fallback to localStorage only
      const savedConfig = localStorage.getItem('tenantConfig')
      if (savedConfig) {
        const config = JSON.parse(savedConfig)
        setTenantConfig(config)
        setIsConfigured(true)
        setCurrentPage('dashboard')
      } else {
        setCurrentPage('config')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfigSave = (config: TenantConfig) => {
    setTenantConfig(config)
    setIsConfigured(true)
    setCurrentPage('dashboard')
    loadData() // Load data after configuration
  }

  const loadData = async () => {
    if (!isConfigured) return
    
    setDataLoading(true)
    try {
      const [statsData, workspacesData, datasetsData] = await Promise.all([
        ApiService.getStats(),
        ApiService.getWorkspaces(50),
        ApiService.getDatasets(undefined, 50)
      ])
      
      setStats(statsData)
      setWorkspaces(workspacesData)
      setDatasets(datasetsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setDataLoading(false)
    }
  }

  const renderMainContent = () => {
    if (!isConfigured && currentPage !== 'config') {
      return (
        <div className="main-content">
          <div className="config-prompt">
            <h2>Configuration Required</h2>
            <p>Please configure your Power BI tenant credentials to get started.</p>
            <button 
              className="btn-primary"
              onClick={() => setCurrentPage('config')}
            >
              Configure Now
            </button>
          </div>
        </div>
      )
    }

    switch (currentPage) {
      case 'config':
        return (
          <div className="main-content">
            <ConfigurationForm 
              onConfigSave={handleConfigSave} 
              initialConfig={tenantConfig ? {
                tenantId: tenantConfig.tenantId,
                clientId: tenantConfig.clientId,
                clientSecret: tenantConfig.clientSecret || ''
              } : undefined}
            />
          </div>
        )
      case 'dashboard':
        return (
          <div className="main-content">
            <div className="page-header">
              <h1>Dashboard</h1>
              <p>Welcome to Power BI Catalog</p>
            </div>
            {isConfigured && (
              <div className="dashboard-content">
                {apiError && (
                  <div className="status-card error">
                    <h3>⚠️ Backend Connection</h3>
                    <p>{apiError}</p>
                  </div>
                )}
                
                <div className="status-card">
                  <h3>Tenant Configuration</h3>
                  <p>✅ Connected to tenant: {tenantConfig?.tenantId}</p>
                  <p>Client ID: {tenantConfig?.clientId}</p>
                  <p>Configuration source: {apiError ? 'Local Storage' : 'Environment File'}</p>
                </div>

                {dataLoading ? (
                  <div className="status-card">
                    <h3>Loading Data...</h3>
                    <div className="loading-spinner"></div>
                  </div>
                ) : stats ? (
                  <>
                    <div className="status-card">
                      <h3>📊 Analysis Overview</h3>
                      <p>Last scan: {stats.latest_run_date ? new Date(stats.latest_run_date).toLocaleDateString() : 'No data'}</p>
                      <p>Total workspaces: <strong>{stats.total_workspaces}</strong></p>
                      <p>Total datasets: <strong>{stats.total_datasets}</strong></p>
                      <p>Total tables: <strong>{stats.total_tables}</strong></p>
                      <p>Total columns: <strong>{stats.total_columns}</strong></p>
                      <p>Total measures: <strong>{stats.total_measures}</strong></p>
                    </div>

                    <div className="status-card">
                      <h3>🏢 Top Workspaces</h3>
                      {workspaces.slice(0, 5).map(ws => (
                        <p key={ws.id}>
                          <strong>{ws.name}</strong> ({ws.datasets_count} datasets)
                          {ws.is_on_dedicated_capacity && <span className="capacity-badge">Premium</span>}
                        </p>
                      ))}
                    </div>

                    <div className="status-card">
                      <h3>📋 Recent Datasets</h3>
                      {datasets.slice(0, 5).map(ds => (
                        <p key={ds.id}>
                          <strong>{ds.name}</strong> in {ds.workspace_name}
                          <br />
                          <small>{ds.tables_count} tables, {ds.measures_count} measures</small>
                        </p>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="status-card">
                    <h3>No Data Available</h3>
                    <p>No Power BI scan data found. Please run a tenant scan first.</p>
                    <button className="btn-primary" onClick={loadData}>Retry Loading</button>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      case 'catalog':
        return (
          <div className="main-content">
            <div className="page-header">
              <h1>Data Catalog</h1>
              <p>Browse and discover your Power BI assets</p>
            </div>
            <div className="coming-soon">
              <h3>Coming Soon</h3>
              <p>The data catalog view will show your scanned Power BI assets.</p>
            </div>
          </div>
        )
      case 'workspaces':
        return (
          <div className="main-content">
            <div className="page-header">
              <h1>Workspaces</h1>
              <p>View and manage Power BI workspaces</p>
            </div>
            <div className="coming-soon">
              <h3>Coming Soon</h3>
              <p>Workspace management features will be available here.</p>
            </div>
          </div>
        )
      case 'datasets':
        return (
          <div className="main-content">
            <div className="page-header">
              <h1>Datasets</h1>
              <p>Explore your Power BI datasets</p>
            </div>
            <div className="coming-soon">
              <h3>Coming Soon</h3>
              <p>Dataset exploration and metadata will be shown here.</p>
            </div>
          </div>
        )
      case 'reports':
        return (
          <div className="main-content">
            <div className="page-header">
              <h1>Reports</h1>
              <p>Browse Power BI reports</p>
            </div>
            <div className="coming-soon">
              <h3>Coming Soon</h3>
              <p>Report catalog and analytics will be available here.</p>
            </div>
          </div>
        )
      case 'search':
        return (
          <div className="main-content">
            <div className="page-header">
              <h1>Search</h1>
              <p>Find Power BI assets quickly</p>
            </div>
            <div className="coming-soon">
              <h3>Coming Soon</h3>
              <p>Advanced search and filtering capabilities.</p>
            </div>
          </div>
        )
      default:
        return (
          <div className="main-content">
            <div className="page-header">
              <h1>Dashboard</h1>
              <p>Welcome to Power BI Catalog</p>
            </div>
          </div>
        )
    }
  }

  if (isLoading) {
    return (
      <div className="app">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <h2>Loading Power BI Catalog...</h2>
          <p>Checking configuration...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />
      <div className="app-content">
        {renderMainContent()}
      </div>
    </div>
  )
}

export default App
