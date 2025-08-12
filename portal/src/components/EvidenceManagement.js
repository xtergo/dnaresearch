import React, { useState, useEffect } from 'react';
import { theoryService } from '../services/api';

const EvidenceManagement = ({ theoryId, theoryVersion, onClose }) => {
  const [evidence, setEvidence] = useState([]);
  const [posterior, setPosterior] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEvidence, setNewEvidence] = useState({
    family_id: '',
    bayes_factor: '',
    evidence_type: 'execution',
    weight: 1.0,
    source: 'manual_entry'
  });

  useEffect(() => {
    if (theoryId && theoryVersion) {
      loadEvidenceData();
    }
  }, [theoryId, theoryVersion]);

  const loadEvidenceData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load evidence trail, posterior, and stats in parallel
      const [evidenceData, posteriorData, statsData] = await Promise.all([
        theoryService.getEvidence(theoryId, theoryVersion),
        theoryService.getPosterior(theoryId, theoryVersion),
        theoryService.getEvidenceStats(theoryId, theoryVersion)
      ]);

      setEvidence(evidenceData.evidence_trail || []);
      setPosterior(posteriorData);
      setStats(statsData);
    } catch (err) {
      setError('Failed to load evidence data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddEvidence = async (e) => {
    e.preventDefault();
    
    if (!newEvidence.family_id || !newEvidence.bayes_factor) {
      setError('Family ID and Bayes Factor are required.');
      return;
    }

    const bayesFactor = parseFloat(newEvidence.bayes_factor);
    if (isNaN(bayesFactor) || bayesFactor <= 0) {
      setError('Bayes Factor must be a positive number.');
      return;
    }

    try {
      await theoryService.addEvidence(
        theoryId,
        theoryVersion,
        newEvidence.family_id,
        bayesFactor,
        newEvidence.evidence_type,
        parseFloat(newEvidence.weight),
        newEvidence.source
      );

      // Reset form
      setNewEvidence({
        family_id: '',
        bayes_factor: '',
        evidence_type: 'execution',
        weight: 1.0,
        source: 'manual_entry'
      });
      setShowAddForm(false);
      
      // Reload data
      await loadEvidenceData();
    } catch (err) {
      setError('Failed to add evidence. Please try again.');
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

  const getEvidenceTypeColor = (evidenceType) => {
    const colors = {
      execution: '#007bff',
      variant_segregation: '#28a745',
      pathway_analysis: '#ffc107',
      literature_review: '#6f42c1',
      manual_entry: '#fd7e14'
    };
    return colors[evidenceType] || '#6c757d';
  };

  if (!theoryId || !theoryVersion) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        color: '#666',
        border: '1px dashed #ddd',
        borderRadius: '4px'
      }}>
        Select a theory to manage evidence
      </div>
    );
  }

  return (
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
        maxWidth: '1000px',
        width: '95%',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3>Evidence Management - {theoryId} v{theoryVersion}</h3>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Close
          </button>
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

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            Loading evidence data...
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Evidence Summary */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                <h4>Evidence Summary</h4>
                <button
                  onClick={() => setShowAddForm(true)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Add Evidence
                </button>
              </div>

              {posterior && (
                <div style={{
                  padding: '15px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '4px',
                  marginBottom: '15px'
                }}>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    <div><strong>Prior:</strong> {posterior.prior}</div>
                    <div><strong>Accumulated BF:</strong> {posterior.accumulated_bf?.toFixed(3)}</div>
                    <div><strong>Posterior:</strong> {posterior.posterior?.toFixed(3)}</div>
                    <div>
                      <strong>Support Class:</strong>
                      <span style={{
                        marginLeft: '8px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        color: 'white',
                        backgroundColor: getSupportClassColor(posterior.support_class)
                      }}>
                        {posterior.support_class}
                      </span>
                    </div>
                    <div><strong>Evidence Count:</strong> {posterior.evidence_count}</div>
                    <div><strong>Families Analyzed:</strong> {posterior.families_analyzed}</div>
                  </div>
                </div>
              )}

              {stats && (
                <div style={{
                  padding: '15px',
                  backgroundColor: '#e7f3ff',
                  borderRadius: '4px',
                  marginBottom: '15px'
                }}>
                  <h5 style={{ margin: '0 0 10px 0' }}>Evidence Statistics</h5>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    <div><strong>Total Evidence:</strong> {stats.total_evidence}</div>
                    <div><strong>Unique Families:</strong> {stats.unique_families}</div>
                    
                    {stats.evidence_types && Object.keys(stats.evidence_types).length > 0 && (
                      <div>
                        <strong>Evidence Types:</strong>
                        <div style={{ marginTop: '5px' }}>
                          {Object.entries(stats.evidence_types).map(([type, count]) => (
                            <span
                              key={type}
                              style={{
                                display: 'inline-block',
                                margin: '2px 5px 2px 0',
                                padding: '2px 8px',
                                backgroundColor: getEvidenceTypeColor(type),
                                color: 'white',
                                borderRadius: '12px',
                                fontSize: '12px'
                              }}
                            >
                              {type}: {count}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {stats.bayes_factor_range && (
                      <div>
                        <strong>Bayes Factor Range:</strong>
                        <div style={{ fontSize: '14px', marginTop: '5px' }}>
                          Min: {stats.bayes_factor_range.min?.toFixed(2)} | 
                          Max: {stats.bayes_factor_range.max?.toFixed(2)} | 
                          Mean: {stats.bayes_factor_range.mean?.toFixed(2)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Evidence Trail */}
            <div>
              <h4>Evidence Trail ({evidence.length})</h4>
              <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                {evidence.length === 0 ? (
                  <div style={{
                    padding: '20px',
                    textAlign: 'center',
                    color: '#666',
                    border: '1px dashed #ddd',
                    borderRadius: '4px'
                  }}>
                    No evidence recorded yet
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: '10px' }}>
                    {evidence.map((item, index) => (
                      <div
                        key={index}
                        style={{
                          padding: '12px',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          backgroundColor: '#fff'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                          <div>
                            <strong>Family:</strong> {item.family_id}
                          </div>
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              color: 'white',
                              backgroundColor: getEvidenceTypeColor(item.evidence_type)
                            }}
                          >
                            {item.evidence_type}
                          </span>
                        </div>
                        
                        <div style={{ display: 'grid', gap: '4px', fontSize: '14px' }}>
                          <div><strong>Bayes Factor:</strong> {item.bayes_factor}</div>
                          <div><strong>Weight:</strong> {item.weight}</div>
                          <div><strong>Source:</strong> {item.source}</div>
                          <div style={{ color: '#666', fontSize: '12px' }}>
                            {new Date(item.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Add Evidence Form */}
        {showAddForm && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100
          }}>
            <div style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              maxWidth: '500px',
              width: '90%'
            }}>
              <h4>Add New Evidence</h4>
              <form onSubmit={handleAddEvidence}>
                <div style={{ display: 'grid', gap: '15px', marginBottom: '20px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                      Family ID *
                    </label>
                    <input
                      type="text"
                      value={newEvidence.family_id}
                      onChange={(e) => setNewEvidence(prev => ({ ...prev, family_id: e.target.value }))}
                      placeholder="e.g., family-001"
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}
                      required
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                      Bayes Factor *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      value={newEvidence.bayes_factor}
                      onChange={(e) => setNewEvidence(prev => ({ ...prev, bayes_factor: e.target.value }))}
                      placeholder="e.g., 2.5"
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}
                      required
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                      Evidence Type
                    </label>
                    <select
                      value={newEvidence.evidence_type}
                      onChange={(e) => setNewEvidence(prev => ({ ...prev, evidence_type: e.target.value }))}
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}
                    >
                      <option value="execution">Execution</option>
                      <option value="variant_segregation">Variant Segregation</option>
                      <option value="pathway_analysis">Pathway Analysis</option>
                      <option value="literature_review">Literature Review</option>
                      <option value="manual_entry">Manual Entry</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                      Weight
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={newEvidence.weight}
                      onChange={(e) => setNewEvidence(prev => ({ ...prev, weight: parseFloat(e.target.value) }))}
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                      Source
                    </label>
                    <input
                      type="text"
                      value={newEvidence.source}
                      onChange={(e) => setNewEvidence(prev => ({ ...prev, source: e.target.value }))}
                      placeholder="e.g., vcf_analysis"
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
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
                  <button
                    type="submit"
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Add Evidence
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidenceManagement;