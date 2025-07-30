import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ConfigurationForm from './components/ConfigurationForm'
import { ApiService, TenantConfigResponse } from './services/api'
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
                <div className="status-card">
                  <h3>Next Steps</h3>
                  <p>• Scan your Power BI tenant for assets</p>
                  <p>• Browse the data catalog</p>
                  <p>• Search for datasets and reports</p>
                </div>
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
