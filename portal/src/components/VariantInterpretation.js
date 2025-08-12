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
    <div className="card">
      <h2>🧬 Variant Interpretation</h2>
      <p className="text-muted mb-3">Analyze genetic variants with clinical significance assessment</p>
      
      <form onSubmit={handleInterpret} className="mb-4">
        <div className="grid grid-2">
          <div className="form-group">
            <label htmlFor="gene-symbol">Gene Symbol *</label>
            <input
              id="gene-symbol"
              type="text"
              value={gene}
              onChange={(e) => setGene(e.target.value)}
              placeholder="e.g., BRCA1, TP53, CFTR"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="variant-notation">Variant (HGVS notation) *</label>
            <input
              id="variant-notation"
              type="text"
              value={variant}
              onChange={(e) => setVariant(e.target.value)}
              placeholder="e.g., c.185delAG, p.Arg273His"
              required
            />
          </div>
        </div>
        
        <button
          type="submit"
          disabled={loading || !gene.trim() || !variant.trim()}
          className="btn btn-primary"
        >
          {loading ? (
            <span className="loading">
              <span className="spinner"></span>
              Interpreting...
            </span>
          ) : (
            '🔬 Interpret Variant'
          )}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>Interpretation Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="card" style={{ border: '2px solid #667eea', background: 'linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%)' }}>
          <h3>📈 Interpretation Results</h3>
          
          <div style={{ display: 'grid', gap: '1.5rem' }}>
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', alignItems: 'center' }}>
              <div>
                <strong>Gene:</strong> <code>{result.gene}</code>
              </div>
              <div>
                <strong>Variant:</strong> <code>{result.variant}</code>
              </div>
              <div>
                <span
                  className="badge"
                  style={{
                    backgroundColor: getImpactColor(result.impact),
                    color: 'white',
                    fontSize: '0.875rem',
                    padding: '0.5rem 1rem'
                  }}
                >
                  {result.impact?.toUpperCase()}
                </span>
              </div>
              <div>
                <span
                  className="badge"
                  style={{
                    backgroundColor: getConfidenceColor(result.confidence),
                    color: 'white',
                    fontSize: '0.875rem',
                    padding: '0.5rem 1rem'
                  }}
                >
                  {result.confidence?.toUpperCase()} CONFIDENCE
                </span>
              </div>
            </div>

            <div className="card" style={{ background: 'linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%)', border: '1px solid #b3d9ff' }}>
              <h4 style={{ margin: '0 0 1rem 0', color: '#0056b3' }}>
                👨‍👩‍👧‍👦 Parent-Friendly Explanation
              </h4>
              <p style={{ margin: 0, lineHeight: '1.6', fontSize: '1.05rem' }}>
                {result.parent_explanation}
              </p>
            </div>

            <div className="card" style={{ background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)', border: '1px solid #dee2e6' }}>
              <h4 style={{ margin: '0 0 1rem 0', color: '#495057' }}>
                🔬 Technical Explanation
              </h4>
              <p style={{ margin: 0, lineHeight: '1.6' }}>
                {result.technical_explanation}
              </p>
            </div>

            {result.recommendations && result.recommendations.length > 0 && (
              <div className="card" style={{ background: 'linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)', border: '1px solid #ffeaa7' }}>
                <h4 style={{ margin: '0 0 1rem 0', color: '#856404' }}>
                  📝 Recommendations:
                </h4>
                <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                  {result.recommendations.map((rec, index) => (
                    <li key={index} style={{ marginBottom: '0.5rem', lineHeight: '1.5' }}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.evidence_sources && result.evidence_sources.length > 0 && (
              <div>
                <h4 style={{ color: '#495057' }}>
                  📚 Evidence Sources:
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                  {result.evidence_sources.map((source, index) => (
                    <span key={index} className="badge badge-info">{source}</span>
                  ))}
                </div>
              </div>
            )}

            {result.population_frequency && (
              <div>
                <strong>🌍 Population Frequency:</strong> 
                <span className="badge badge-secondary ml-2">{result.population_frequency}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VariantInterpretation;