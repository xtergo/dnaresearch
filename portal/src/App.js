import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import { theoryService } from './services/api';
import authService from './services/auth';
import GeneSearch from './components/GeneSearch';
import VariantInterpretation from './components/VariantInterpretation';
import TheoryManagement from './components/TheoryManagement';
import FileUpload from './components/FileUpload';
import Login from './components/Login';

const THEORY_TEMPLATE = {
  id: "",
  version: "1.0.0",
  scope: "autism",
  criteria: {
    genes: [],
    pathways: [],
    phenotypes: []
  },
  evidence_model: {
    priors: 0.1,
    likelihood_weights: {
      variant_hit: 1.0,
      segregation: 2.0,
      pathway: 1.5
    }
  }
};

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [formData, setFormData] = useState({
    id: '',
    version: '1.0.0',
    scope: 'autism',
    genes: '',
    pathways: '',
    phenotypes: ''
  });
  const [jsonData, setJsonData] = useState(JSON.stringify(THEORY_TEMPLATE, null, 2));
  const [validationError, setValidationError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFormChange = (field, value) => {
    const newFormData = { ...formData, [field]: value };
    setFormData(newFormData);
    
    // Update JSON based on form
    const theory = {
      ...THEORY_TEMPLATE,
      id: newFormData.id,
      version: newFormData.version,
      scope: newFormData.scope,
      criteria: {
        genes: newFormData.genes.split(',').map(g => g.trim()).filter(g => g),
        pathways: newFormData.pathways.split(',').map(p => p.trim()).filter(p => p),
        phenotypes: newFormData.phenotypes.split(',').map(p => p.trim()).filter(p => p)
      }
    };
    setJsonData(JSON.stringify(theory, null, 2));
  };

  const handleJsonChange = (value) => {
    setJsonData(value);
    try {
      const parsed = JSON.parse(value);
      setFormData({
        id: parsed.id || '',
        version: parsed.version || '1.0.0',
        scope: parsed.scope || 'autism',
        genes: (parsed.criteria?.genes || []).join(', '),
        pathways: (parsed.criteria?.pathways || []).join(', '),
        phenotypes: (parsed.criteria?.phenotypes || []).join(', ')
      });
      setValidationError('');
    } catch (e) {
      setValidationError('Invalid JSON format');
    }
  };

  const validateTheory = (theory) => {
    if (!theory.id) return 'Theory ID is required';
    if (!/^[a-z0-9-]+$/.test(theory.id)) return 'Theory ID must contain only lowercase letters, numbers, and hyphens';
    if (!/^\d+\.\d+\.\d+$/.test(theory.version)) return 'Version must be in semantic version format (e.g., 1.0.0)';
    if (!['autism', 'cancer', 'cardiovascular', 'neurological', 'metabolic'].includes(theory.scope)) {
      return 'Scope must be one of: autism, cancer, cardiovascular, neurological, metabolic';
    }
    return null;
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setValidationError('');
    setSuccessMessage('');

    try {
      const theory = JSON.parse(jsonData);
      const error = validateTheory(theory);
      if (error) {
        setValidationError(error);
        setIsSubmitting(false);
        return;
      }

      await theoryService.createTheory(theory);
      setSuccessMessage(`Theory "${theory.id}" created successfully!`);
      
      // Reset form
      setFormData({
        id: '',
        version: '1.0.0',
        scope: 'autism',
        genes: '',
        pathways: '',
        phenotypes: ''
      });
      setJsonData(JSON.stringify(THEORY_TEMPLATE, null, 2));
    } catch (error) {
      setValidationError(error.response?.data?.detail || 'Failed to create theory');
    }
    setIsSubmitting(false);
  };

  // Check authentication on app load
  useEffect(() => {
    const checkAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error('Auth check failed:', error);
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  const handleLogin = (userData, token) => {
    setUser(userData);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
  };

  const tabStyle = (isActive) => ({
    className: isActive ? 'active' : ''
  });

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div>
      <div className="header">
        <div className="container">
          <div className="header-content">
            <div>
              <h1>🧬 DNA Research Platform</h1>
              <p>Genomic analysis and theory management</p>
            </div>
            <div className="user-info">
              <span>Welcome, {user.username} ({user.role})</span>
              <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
            </div>
          </div>
          <nav style={{ marginTop: '20px' }}>
            <button
              className={activeTab === 'search' ? 'active' : ''}
              onClick={() => setActiveTab('search')}
            >
              🔍 Gene Search
            </button>
            <button
              className={activeTab === 'interpret' ? 'active' : ''}
              onClick={() => setActiveTab('interpret')}
            >
              🧬 Variant Interpretation
            </button>
            <button
              className={activeTab === 'theories' ? 'active' : ''}
              onClick={() => setActiveTab('theories')}
            >
              📊 Theory Management
            </button>
            <button
              className={activeTab === 'upload' ? 'active' : ''}
              onClick={() => setActiveTab('upload')}
            >
              📁 File Upload
            </button>
            <button
              className={activeTab === 'theory' ? 'active' : ''}
              onClick={() => setActiveTab('theory')}
            >
              ⚗️ Theory Creation
            </button>
          </nav>
        </div>
      </div>
      
      <div className="container">
        {activeTab === 'search' && (
          <div className="fade-in">
            <GeneSearch />
          </div>
        )}
        {activeTab === 'interpret' && (
          <div className="fade-in">
            <VariantInterpretation />
          </div>
        )}
        {activeTab === 'theories' && (
          <div className="fade-in">
            <TheoryManagement />
          </div>
        )}
        {activeTab === 'upload' && (
          <div className="fade-in">
            <FileUpload />
          </div>
        )}
        
        {activeTab === 'theory' && (
          <div className="card fade-in">
            <h2>Theory Creation</h2>
            {successMessage && (
              <div className="success-message">{successMessage}</div>
            )}
            {validationError && (
              <div className="error-message">{validationError}</div>
            )}
        
        <div className="grid grid-2">
          <div className="card">
            <h3>Theory Form</h3>
            
            <div className="form-group">
              <label>Theory ID</label>
              <input
                type="text"
                value={formData.id}
                onChange={(e) => handleFormChange('id', e.target.value)}
                placeholder="e.g., shank3-autism-theory"
              />
            </div>
            
            <div className="form-group">
              <label>Version</label>
              <input
                type="text"
                value={formData.version}
                onChange={(e) => handleFormChange('version', e.target.value)}
                placeholder="1.0.0"
              />
            </div>
            
            <div className="form-group">
              <label>Scope</label>
              <select
                value={formData.scope}
                onChange={(e) => handleFormChange('scope', e.target.value)}
              >
                <option value="autism">Autism</option>
                <option value="cancer">Cancer</option>
                <option value="cardiovascular">Cardiovascular</option>
                <option value="neurological">Neurological</option>
                <option value="metabolic">Metabolic</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Genes (comma-separated)</label>
              <input
                type="text"
                value={formData.genes}
                onChange={(e) => handleFormChange('genes', e.target.value)}
                placeholder="SHANK3, NRXN1, SYNGAP1"
              />
            </div>
            
            <div className="form-group">
              <label>Pathways (comma-separated)</label>
              <input
                type="text"
                value={formData.pathways}
                onChange={(e) => handleFormChange('pathways', e.target.value)}
                placeholder="synaptic_transmission, neuronal_development"
              />
            </div>
            
            <div className="form-group">
              <label>Phenotypes (comma-separated)</label>
              <input
                type="text"
                value={formData.phenotypes}
                onChange={(e) => handleFormChange('phenotypes', e.target.value)}
                placeholder="intellectual_disability, autism_spectrum_disorder"
              />
            </div>
          </div>
          
          <div className="card">
            <h3>JSON Editor</h3>
            <div className="editor-container">
              <Editor
                height="400px"
                defaultLanguage="json"
                value={jsonData}
                onChange={handleJsonChange}
                options={{
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 12
                }}
              />
            </div>
          </div>
        </div>
        

        
        <div className="mt-4">
          <button 
            className="btn btn-primary" 
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span className="loading">
                <span className="spinner"></span>
                Creating...
              </span>
            ) : (
              'Create Theory'
            )}
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => {
              setFormData({
                id: '',
                version: '1.0.0',
                scope: 'autism',
                genes: '',
                pathways: '',
                phenotypes: ''
              });
              setJsonData(JSON.stringify(THEORY_TEMPLATE, null, 2));
              setValidationError('');
              setSuccessMessage('');
            }}
          >
            Reset
          </button>
        </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;