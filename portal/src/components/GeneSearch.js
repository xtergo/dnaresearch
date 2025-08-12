import React, { useState } from 'react';
import { geneService } from '../services/api';

const GeneSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedGene, setSelectedGene] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      const data = await geneService.searchGenes(query);
      setResults(data.results || []);
    } catch (err) {
      setError('Failed to search genes. Please try again.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneSelect = async (gene) => {
    try {
      const details = await geneService.getGeneDetails(gene.symbol);
      setSelectedGene(details);
    } catch (err) {
      setError('Failed to load gene details.');
    }
  };

  return (
    <div className="card">
      <h2>🔬 Gene Search</h2>
      <p className="text-muted mb-3">Search for genes by symbol, alias, or genomic coordinates</p>
      
      <form onSubmit={handleSearch} className="mb-4">
        <div className="form-group">
          <label htmlFor="gene-search">Gene Query</label>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              id="gene-search"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search genes (e.g., BRCA1, autism, 22:51150000-51180000)"
              style={{ flex: 1 }}
              required
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="btn btn-primary"
            >
              {loading ? (
                <span className="loading">
                  <span className="spinner"></span>
                  Searching...
                </span>
              ) : (
                '🔍 Search'
              )}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>Search Error:</strong> {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="mb-4">
          <h3>Search Results ({results.length})</h3>
          <div className="search-results">
            {results.map((gene, index) => (
              <div
                key={index}
                onClick={() => handleGeneSelect(gene)}
                className="search-result-item"
                role="button"
                tabIndex={0}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleGeneSelect(gene);
                  }
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '1.125rem', color: '#2c3e50' }}>
                  {gene.symbol}
                </div>
                <div style={{ color: '#666', marginBottom: '0.5rem' }}>
                  {gene.name}
                </div>
                <div className="mb-2">
                  <span className="badge badge-info mr-2">📍 {gene.location}</span>
                  <span className="badge badge-secondary">🎯 {gene.match_type}</span>
                </div>
                {gene.description && (
                  <div style={{ fontSize: '0.9rem', color: '#555', lineHeight: '1.4' }}>
                    {gene.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedGene && (
        <div className="card" style={{ border: '2px solid #667eea', background: 'linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%)' }}>
          <h3>🧬 Gene Details: {selectedGene.symbol}</h3>
          <div className="grid" style={{ gap: '1rem' }}>
            <div><strong>Name:</strong> {selectedGene.name}</div>
            <div><strong>Chromosome:</strong> <span className="badge badge-primary">{selectedGene.chromosome}</span></div>
            <div><strong>Location:</strong> <code>{selectedGene.location}</code></div>
            {selectedGene.aliases && selectedGene.aliases.length > 0 && (
              <div>
                <strong>Aliases:</strong>
                <div className="mt-1">
                  {selectedGene.aliases.map((alias, idx) => (
                    <span key={idx} className="badge badge-secondary mr-1">{alias}</span>
                  ))}
                </div>
              </div>
            )}
            {selectedGene.description && (
              <div>
                <strong>Description:</strong>
                <p className="mt-1" style={{ lineHeight: '1.5' }}>{selectedGene.description}</p>
              </div>
            )}
            {selectedGene.pathways && selectedGene.pathways.length > 0 && (
              <div>
                <strong>Pathways:</strong>
                <div className="mt-1">
                  {selectedGene.pathways.map((pathway, idx) => (
                    <span key={idx} className="badge badge-success mr-1">🔬 {pathway}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      {!loading && !error && results.length === 0 && query && (
        <div className="info-message text-center">
          <strong>No results found</strong><br />
          Try searching with different terms or check your spelling.
        </div>
      )}
    </div>
  );
};

export default GeneSearch;