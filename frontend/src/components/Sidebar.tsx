import React, { useState } from 'react';
import './Sidebar.css';

interface SidebarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentPage, onPageChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'catalog', label: 'Data Catalog', icon: '📋' },
    { id: 'workspaces', label: 'Workspaces', icon: '🏢' },
    { id: 'datasets', label: 'Datasets', icon: '🗃️' },
    { id: 'reports', label: 'Reports', icon: '📈' },
    { id: 'search', label: 'Search', icon: '🔍' },
    { id: 'config', label: 'Configuration', icon: '⚙️' },
  ];

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <span className="logo-icon">⚡</span>
          {!isCollapsed && <span className="logo-text">Power BI Catalog</span>}
        </div>
        <button 
          className="collapse-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? '→' : '←'}
        </button>
      </div>

      <nav className="sidebar-nav">
        <ul className="nav-list">
          {menuItems.map((item) => (
            <li key={item.id} className="nav-item">
              <button
                className={`nav-link ${currentPage === item.id ? 'active' : ''}`}
                onClick={() => onPageChange(item.id)}
                title={isCollapsed ? item.label : undefined}
              >
                <span className="nav-icon">{item.icon}</span>
                {!isCollapsed && <span className="nav-text">{item.label}</span>}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        {!isCollapsed && (
          <div className="footer-info">
            <p className="version">v1.0.0</p>
            <p className="copyright">© 2025 Power BI Catalog</p>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;