import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';
import './ConfigurationForm.css';

interface TenantConfig {
  tenantId: string;
  clientId: string;
  clientSecret: string;
}

interface ConfigurationFormProps {
  onConfigSave: (config: TenantConfig) => void;
  initialConfig?: Partial<TenantConfig>;
}

const ConfigurationForm: React.FC<ConfigurationFormProps> = ({ onConfigSave, initialConfig }) => {
  const [config, setConfig] = useState<TenantConfig>({
    tenantId: '',
    clientId: '',
    clientSecret: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<TenantConfig>>({});
  const [hasPrefilledSecret, setHasPrefilledSecret] = useState(false);

  // Load configuration from props or localStorage
  useEffect(() => {
    if (initialConfig) {
      // Use configuration passed from parent (from backend)
      const isSecretPrefilled = initialConfig.clientSecret?.startsWith('••••••••');
      setConfig({
        tenantId: initialConfig.tenantId || '',
        clientId: initialConfig.clientId || '',
        clientSecret: initialConfig.clientSecret || ''
      });
      setHasPrefilledSecret(isSecretPrefilled || false);
    } else {
      // Fallback to localStorage
      const savedConfig = localStorage.getItem('tenantConfig');
      if (savedConfig) {
        const parsedConfig = JSON.parse(savedConfig);
        setConfig(parsedConfig);
        setHasPrefilledSecret(false);
      }
    }
  }, [initialConfig]);

  const validateForm = (): boolean => {
    const newErrors: Partial<TenantConfig> = {};
    
    if (!config.tenantId.trim()) {
      newErrors.tenantId = 'Tenant ID is required';
    }
    
    if (!config.clientId.trim()) {
      newErrors.clientId = 'Client ID is required';
    }
    
    if (!config.clientSecret.trim() || (hasPrefilledSecret && config.clientSecret.startsWith('••••••••'))) {
      newErrors.clientSecret = hasPrefilledSecret ? 
        'Please enter your actual client secret' : 
        'Client Secret is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    
    try {
      // Try to validate with backend first
      try {
        await ApiService.updateConfig({
          tenant_id: config.tenantId,
          client_id: config.clientId,
          client_secret: config.clientSecret
        });
        console.log('Configuration validated with backend');
      } catch (apiError) {
        console.warn('Backend validation failed, saving locally only:', apiError);
      }
      
      // Save to localStorage
      localStorage.setItem('tenantConfig', JSON.stringify(config));
      
      // Call parent callback
      onConfigSave(config);
      
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Error saving configuration:', error);
      alert('Error saving configuration. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof TenantConfig, value: string) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  const handleClear = () => {
    setConfig({
      tenantId: '',
      clientId: '',
      clientSecret: ''
    });
    localStorage.removeItem('tenantConfig');
    setErrors({});
  };

  return (
    <div className="config-form-container">
      <div className="config-form-header">
        <h2>Power BI Tenant Configuration</h2>
        <p>Enter your Azure AD service principal credentials to connect to your Power BI tenant.</p>
        {initialConfig && (
          <div className="preload-notice">
            <p><strong>✅ Configuration loaded from environment file</strong></p>
            <p>Some values have been pre-filled from your .env file. You can modify them if needed.</p>
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="config-form">
        <div className="form-group">
          <label htmlFor="tenantId">Tenant ID</label>
          <input
            type="text"
            id="tenantId"
            value={config.tenantId}
            onChange={(e) => handleInputChange('tenantId', e.target.value)}
            placeholder="e.g., f66009f9-3aae-4a4e-9161-974b63e7eb6a"
            className={errors.tenantId ? 'error' : ''}
          />
          {errors.tenantId && <span className="error-message">{errors.tenantId}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="clientId">Client ID</label>
          <input
            type="text"
            id="clientId"
            value={config.clientId}
            onChange={(e) => handleInputChange('clientId', e.target.value)}
            placeholder="e.g., d3590ed6-52b3-4102-aeff-aad2292ab01c"
            className={errors.clientId ? 'error' : ''}
          />
          {errors.clientId && <span className="error-message">{errors.clientId}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="clientSecret">Client Secret</label>
          <input
            type="password"
            id="clientSecret"
            value={config.clientSecret}
            onChange={(e) => handleInputChange('clientSecret', e.target.value)}
            placeholder={hasPrefilledSecret ? "Secret loaded from environment - replace if needed" : "Enter your client secret"}
            className={errors.clientSecret ? 'error' : ''}
          />
          {hasPrefilledSecret && !errors.clientSecret && (
            <span className="info-message">✅ Secret loaded from environment file</span>
          )}
          {errors.clientSecret && <span className="error-message">{errors.clientSecret}</span>}
        </div>

        <div className="form-actions">
          <button type="button" onClick={handleClear} className="btn-secondary">
            Clear
          </button>
          <button type="submit" disabled={isLoading} className="btn-primary">
            {isLoading ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
      
      <div className="config-form-help">
        <h4>How to get these values:</h4>
        <ol>
          <li>Go to Azure Active Directory in the Azure portal</li>
          <li>Navigate to "App registrations" and select your application</li>
          <li>Copy the "Application (client) ID" and "Directory (tenant) ID"</li>
          <li>Go to "Certificates & secrets" to create or copy a client secret</li>
        </ol>
      </div>
    </div>
  );
};

export default ConfigurationForm;