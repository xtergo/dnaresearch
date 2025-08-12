import React, { useState } from 'react';
import { geneService } from '../services/api';

const VariantInterpretation = () => {
  const [gene, setGene] = useState('');
  const [variant, setVariant] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInterpret = async (e) => {
    e.preventDefault();
    if (!gene.trim() || !variant.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      const data = await geneService.interpretVariant(gene, variant);
      setResult(data);
    } catch (err) {
      setError('Failed to interpret variant. Please check your input.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const getImpactColor = (impact) => {
    switch (impact?.toLowerCase()) {
      case 'pathogenic': return '#dc3545';
      case 'likely_pathogenic': return '#fd7e14';
      case 'uncertain': return '#ffc107';
      case 'likely_benign': return '#28a745';
      case 'benign': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence?.toLowerCase()) {
      case 'high': return '#28a745';
      case 'medium': return '#ffc107';
      case 'low': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Variant Interpretation</h2>
      
      <form onSubmit={handleInterpret} style={{ marginBottom: '20px' }}>
        <div style={{ display: 'grid', gap: '15px', marginBottom: '20px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Gene Symbol:
            </label>
            <input
              type="text"
              value={gene}
              onChange={(e) => setGene(e.target.value)}
              placeholder="e.g., BRCA1"
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px'
              }}
            />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Variant (HGVS notation):
            </label>
            <input
              type="text"
              value={variant}
              onChange={(e) => setVariant(e.target.value)}
              placeholder="e.g., c.185delAG"
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px'
              }}
            />
          </div>
        </div>
        
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '12px 24px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '16px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Interpreting...' : 'Interpret Variant'}
        </button>
      </form>

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

      {result && (
        <div style={{
          padding: '20px',
          border: '2px solid #007bff',
          borderRadius: '8px',
          backgroundColor: '#f8f9fa'
        }}>
          <h3>Interpretation Results</h3>
          
          <div style={{ display: 'grid', gap: '15px' }}>
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
              <div>
                <strong>Gene:</strong> {result.gene}
              </div>
              <div>
                <strong>Variant:</strong> {result.variant}
              </div>
              <div>
                <span
                  style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    color: 'white',
                    backgroundColor: getImpactColor(result.impact),
                    fontSize: '14px',
                    fontWeight: 'bold'
                  }}
                >
                  {result.impact?.toUpperCase()}
                </span>
              </div>
              <div>
                <span
                  style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    color: 'white',
                    backgroundColor: getConfidenceColor(result.confidence),
                    fontSize: '14px'
                  }}
                >
                  {result.confidence?.toUpperCase()} CONFIDENCE
                </span>
              </div>
            </div>

            <div style={{
              padding: '15px',
              backgroundColor: '#e7f3ff',
              borderRadius: '4px',
              border: '1px solid #b3d9ff'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#0056b3' }}>
                Parent-Friendly Explanation
              </h4>
              <p style={{ margin: 0, lineHeight: '1.5' }}>
                {result.parent_explanation}
              </p>
            </div>

            <div style={{
              padding: '15px',
              backgroundColor: '#f0f0f0',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>
                Technical Explanation
              </h4>
              <p style={{ margin: 0, lineHeight: '1.5' }}>
                {result.technical_explanation}
              </p>
            </div>

            {result.recommendations && result.recommendations.length > 0 && (
              <div>
                <h4>Recommendations:</h4>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {result.recommendations.map((rec, index) => (
                    <li key={index} style={{ marginBottom: '5px' }}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.evidence_sources && result.evidence_sources.length > 0 && (
              <div>
                <h4>Evidence Sources:</h4>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {result.evidence_sources.map((source, index) => (
                    <li key={index} style={{ marginBottom: '5px' }}>{source}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.population_frequency && (
              <div>
                <strong>Population Frequency:</strong> {result.population_frequency}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VariantInterpretation;