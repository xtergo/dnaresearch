import React, { useState, useEffect } from 'react';
import { theoryService } from '../services/api';
import EvidenceManagement from './EvidenceManagement';

const TheoryManagement = () => {
  const [theories, setTheories] = useState([]);
  const [selectedTheory, setSelectedTheory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    scope: '',
    author: '',
    search: '',
    sort_by: 'posterior',
    sort_order: 'desc'
  });
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTheory, setEditingTheory] = useState(null);
  const [showEvidenceManager, setShowEvidenceManager] = useState(null);

  useEffect(() => {
    loadTheories();
  }, [filters]);

  const loadTheories = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await theoryService.listTheories(filters);
      setTheories(data.theories || []);
    } catch (err) {
      setError('Failed to load theories. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleTheorySelect = async (theory) => {
    try {
      const details = await theoryService.getTheoryDetails(theory.id, theory.version);
      setSelectedTheory(details);
    } catch (err) {
      setError('Failed to load theory details.');
    }
  };

  const handleDeleteTheory = async (theoryId, version) => {
    if (!window.confirm('Are you sure you want to delete this theory?')) return;
    
    try {
      await theoryService.deleteTheory(theoryId, version);
      await loadTheories();
      if (selectedTheory && selectedTheory.id === theoryId) {
        setSelectedTheory(null);
      }
    } catch (err) {
      setError('Failed to delete theory.');
    }
  };

  const getSupportClassColor = (supportClass) => {
    switch (supportClass?.toLowerCase()) {
      case 'strong': return '#28a745';
      case 'moderate': return '#ffc107';
      case 'weak': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getScopeColor = (scope) => {
    const colors = {
      autism: '#007bff',
      cancer: '#dc3545',
      cardiovascular: '#fd7e14',
      neurological: '#6f42c1',
      metabolic: '#20c997'
    };
    return colors[scope] || '#6c757d';
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Theory Management</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Create New Theory
        </button>
      </div>

      {/* Filters */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '20px',
        padding: '15px',
        backgroundColor: '#f8f9fa',
        borderRadius: '4px'
      }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Scope:
          </label>
          <select
            value={filters.scope}
            onChange={(e) => handleFilterChange('scope', e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          >
            <option value="">All Scopes</option>
            <option value="autism">Autism</option>
            <option value="cancer">Cancer</option>
            <option value="cardiovascular">Cardiovascular</option>
            <option value="neurological">Neurological</option>
            <option value="metabolic">Metabolic</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Author:
          </label>
          <input
            type="text"
            value={filters.author}
            onChange={(e) => handleFilterChange('author', e.target.value)}
            placeholder="Filter by author"
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Search:
          </label>
          <input
            type="text"
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            placeholder="Search theories..."
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Sort By:
          </label>
          <select
            value={filters.sort_by}
            onChange={(e) => handleFilterChange('sort_by', e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          >
            <option value="posterior">Posterior</option>
            <option value="evidence_count">Evidence Count</option>
            <option value="created_at">Created Date</option>
            <option value="updated_at">Updated Date</option>
            <option value="title">Title</option>
          </select>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Theory List */}
        <div>
          <h3>Theories ({theories.length})</h3>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>Loading...</div>
          ) : (
            <div style={{ display: 'grid', gap: '10px', maxHeight: '600px', overflowY: 'auto' }}>
              {theories.map((theory) => (
                <div
                  key={`${theory.id}-${theory.version}`}
                  onClick={() => handleTheorySelect(theory)}
                  style={{
                    padding: '15px',
                    border: selectedTheory?.id === theory.id ? '2px solid #007bff' : '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    backgroundColor: selectedTheory?.id === theory.id ? '#f0f8ff' : '#fff'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '5px' }}>
                        {theory.title || theory.id}
                      </div>
                      <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
                        ID: {theory.id} | Version: {theory.version}
                      </div>
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '8px' }}>
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            color: 'white',
                            backgroundColor: getScopeColor(theory.scope)
                          }}
                        >
                          {theory.scope}
                        </span>
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            color: 'white',
                            backgroundColor: getSupportClassColor(theory.support_class)
                          }}
                        >
                          {theory.support_class}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#888' }}>
                        Author: {theory.author} | Evidence: {theory.evidence_count} | Posterior: {theory.posterior?.toFixed(3)}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '5px' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowEvidenceManager({ id: theory.id, version: theory.version });
                        }}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#007bff',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer'
                        }}
                      >
                        Evidence
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingTheory(theory);
                        }}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#ffc107',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer'
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteTheory(theory.id, theory.version);
                        }}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#dc3545',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer'
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Theory Details */}
        <div>
          <h3>Theory Details</h3>
          {selectedTheory ? (
            <div style={{
              padding: '20px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ marginBottom: '15px' }}>
                <h4 style={{ margin: '0 0 10px 0' }}>{selectedTheory.title || selectedTheory.id}</h4>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  ID: {selectedTheory.id} | Version: {selectedTheory.version}
                </div>
              </div>

              <div style={{ display: 'grid', gap: '10px', marginBottom: '15px' }}>
                <div><strong>Scope:</strong> {selectedTheory.scope}</div>
                <div><strong>Author:</strong> {selectedTheory.author}</div>
                <div><strong>Lifecycle:</strong> {selectedTheory.lifecycle}</div>
                <div><strong>Support Class:</strong> 
                  <span style={{
                    marginLeft: '8px',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    color: 'white',
                    backgroundColor: getSupportClassColor(selectedTheory.support_class)
                  }}>
                    {selectedTheory.support_class}
                  </span>
                </div>
                <div><strong>Posterior:</strong> {selectedTheory.posterior?.toFixed(3)}</div>
                <div><strong>Evidence Count:</strong> {selectedTheory.evidence_count}</div>
                <div><strong>Has Comments:</strong> {selectedTheory.has_comments ? 'Yes' : 'No'}</div>
              </div>

              {selectedTheory.tags && selectedTheory.tags.length > 0 && (
                <div style={{ marginBottom: '15px' }}>
                  <strong>Tags:</strong>
                  <div style={{ marginTop: '5px' }}>
                    {selectedTheory.tags.map((tag, index) => (
                      <span
                        key={index}
                        style={{
                          display: 'inline-block',
                          margin: '2px 5px 2px 0',
                          padding: '2px 8px',
                          backgroundColor: '#e9ecef',
                          borderRadius: '12px',
                          fontSize: '12px'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ fontSize: '12px', color: '#888' }}>
                <div>Created: {new Date(selectedTheory.created_at).toLocaleString()}</div>
                <div>Updated: {new Date(selectedTheory.updated_at).toLocaleString()}</div>
              </div>
            </div>
          ) : (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              color: '#666',
              border: '1px dashed #ddd',
              borderRadius: '4px'
            }}>
              Select a theory to view details
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Theory Modal would go here */}
      {(showCreateForm || editingTheory) && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}>
            <h3>{editingTheory ? 'Edit Theory' : 'Create New Theory'}</h3>
            <p>Theory creation/editing form would be implemented here...</p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingTheory(null);
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evidence Management Modal */}
      {showEvidenceManager && (
        <EvidenceManagement
          theoryId={showEvidenceManager.id}
          theoryVersion={showEvidenceManager.version}
          onClose={() => setShowEvidenceManager(null)}
        />
      )}
    </div>
  );
};

export default TheoryManagement;