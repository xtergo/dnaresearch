import React, { useState, useEffect } from 'react';
import api from '../services/api';

const ConsentManagement = ({ userId = 'user_001' }) => {
  const [consents, setConsents] = useState([]);
  const [forms, setForms] = useState([]);
  const [selectedForm, setSelectedForm] = useState(null);
  const [userData, setUserData] = useState({
    full_name: '',
    email: '',
    date_of_birth: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadConsentData();
  }, [userId]);

  const loadConsentData = async () => {
    try {
      setLoading(true);
      const [formsRes, consentsRes] = await Promise.all([
        api.get('/consent/forms'),
        api.get(`/consent/users/${userId}`)
      ]);
      setForms(formsRes.data.forms);
      setConsents(consentsRes.data.consents);
    } catch (err) {
      setError('Failed to load consent data');
    } finally {
      setLoading(false);
    }
  };

  const handleGrantConsent = async (e) => {
    e.preventDefault();
    if (!selectedForm) return;

    try {
      setLoading(true);
      setError('');
      
      const signature = `sig_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      await api.post('/consent/capture', {
        form_id: selectedForm.form_id,
        user_id: userId,
        user_data: userData,
        digital_signature: signature
      });

      setSuccess('Consent granted successfully');
      setSelectedForm(null);
      setUserData({ full_name: '', email: '', date_of_birth: '' });
      await loadConsentData();
    } catch (err) {
      setError(err.message || 'Failed to grant consent');
    } finally {
      setLoading(false);
    }
  };

  const handleWithdrawConsent = async (consentType) => {
    try {
      setLoading(true);
      setError('');
      
      await api.post('/consent/withdraw', {
        user_id: userId,
        consent_type: consentType,
        reason: 'user_request'
      });

      setSuccess('Consent withdrawn successfully');
      await loadConsentData();
    } catch (err) {
      setError(err.message || 'Failed to withdraw consent');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#28a745';
      case 'withdrawn': return '#dc3545';
      case 'expired': return '#ffc107';
      default: return '#6c757d';
    }
  };

  if (loading && consents.length === 0) {
    return <div className="consent-loading">Loading consent data...</div>;
  }

  return (
    <div className="consent-management">
      <h2>🔒 Consent Management</h2>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="consent-status">
        <h3>Current Consent Status</h3>
        {consents.length === 0 ? (
          <p>No consent records found</p>
        ) : (
          <div className="consent-list">
            {consents.map(consent => (
              <div key={consent.consent_id} className="consent-item">
                <div className="consent-header">
                  <span className="consent-type">{consent.consent_type.replace('_', ' ')}</span>
                  <span 
                    className="consent-status-badge"
                    style={{ backgroundColor: getStatusColor(consent.status) }}
                  >
                    {consent.status}
                  </span>
                </div>
                <div className="consent-details">
                  <small>Granted: {new Date(consent.granted_at).toLocaleDateString()}</small>
                  {consent.expires_at && (
                    <small>Expires: {new Date(consent.expires_at).toLocaleDateString()}</small>
                  )}
                  {consent.status === 'active' && (
                    <button 
                      onClick={() => handleWithdrawConsent(consent.consent_type)}
                      className="btn btn-danger btn-sm"
                      disabled={loading}
                    >
                      Withdraw
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="consent-forms">
        <h3>Grant New Consent</h3>
        {!selectedForm ? (
          <div className="form-selection">
            {forms.map(form => (
              <div key={form.form_id} className="form-option">
                <h4>{form.title}</h4>
                <p>{form.description}</p>
                <button 
                  onClick={() => setSelectedForm(form)}
                  className="btn btn-primary"
                >
                  Grant Consent
                </button>
              </div>
            ))}
          </div>
        ) : (
          <form onSubmit={handleGrantConsent} className="consent-form">
            <h4>{selectedForm.title}</h4>
            <div className="consent-text">
              <p>{selectedForm.consent_text || selectedForm.description}</p>
            </div>
            
            {selectedForm.required_fields.map(field => (
              <div key={field} className="form-group">
                <label>{field.replace('_', ' ')}</label>
                <input
                  type={field === 'email' ? 'email' : field === 'date_of_birth' ? 'date' : 'text'}
                  value={userData[field] || ''}
                  onChange={(e) => setUserData({...userData, [field]: e.target.value})}
                  required
                />
              </div>
            ))}

            <div className="form-actions">
              <button type="submit" disabled={loading} className="btn btn-success">
                {loading ? 'Processing...' : 'Grant Consent'}
              </button>
              <button 
                type="button" 
                onClick={() => setSelectedForm(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      <style jsx>{`
        .consent-management {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        .consent-item {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 15px;
          margin-bottom: 10px;
        }
        .consent-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .consent-type {
          font-weight: bold;
          text-transform: capitalize;
        }
        .consent-status-badge {
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          text-transform: uppercase;
        }
        .consent-details {
          display: flex;
          gap: 15px;
          align-items: center;
        }
        .form-option {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 15px;
          margin-bottom: 15px;
        }
        .consent-form {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 20px;
        }
        .consent-text {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 4px;
          margin: 15px 0;
          border-left: 4px solid #007bff;
        }
        .form-group {
          margin-bottom: 15px;
        }
        .form-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: bold;
          text-transform: capitalize;
        }
        .form-group input {
          width: 100%;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }
        .form-actions {
          display: flex;
          gap: 10px;
          margin-top: 20px;
        }
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }
        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-sm { padding: 4px 8px; font-size: 12px; }
        .error-message {
          background: #f8d7da;
          color: #721c24;
          padding: 10px;
          border-radius: 4px;
          margin-bottom: 15px;
        }
        .success-message {
          background: #d4edda;
          color: #155724;
          padding: 10px;
          border-radius: 4px;
          margin-bottom: 15px;
        }
        .consent-loading {
          text-align: center;
          padding: 40px;
          color: #6c757d;
        }
      `}</style>
    </div>
  );
};

export default ConsentManagement;