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
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Gene Search</h2>
      
      <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search genes (e.g., BRCA1, autism, 22:51150000-51180000)"
            style={{
              flex: 1,
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '16px'
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div style={{
          padding: '10px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Search Results ({results.length})</h3>
          <div style={{ display: 'grid', gap: '10px' }}>
            {results.map((gene, index) => (
              <div
                key={index}
                onClick={() => handleGeneSelect(gene)}
                style={{
                  padding: '15px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  backgroundColor: '#f8f9fa'
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '18px' }}>
                  {gene.symbol}
                </div>
                <div style={{ color: '#666', marginBottom: '5px' }}>
                  {gene.name}
                </div>
                <div style={{ fontSize: '14px', color: '#888' }}>
                  Location: {gene.location} | Match: {gene.match_type}
                </div>
                {gene.description && (
                  <div style={{ fontSize: '14px', marginTop: '5px' }}>
                    {gene.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedGene && (
        <div style={{
          padding: '20px',
          border: '2px solid #007bff',
          borderRadius: '8px',
          backgroundColor: '#f0f8ff'
        }}>
          <h3>Gene Details: {selectedGene.symbol}</h3>
          <div style={{ display: 'grid', gap: '10px' }}>
            <div><strong>Name:</strong> {selectedGene.name}</div>
            <div><strong>Chromosome:</strong> {selectedGene.chromosome}</div>
            <div><strong>Location:</strong> {selectedGene.location}</div>
            {selectedGene.aliases && (
              <div><strong>Aliases:</strong> {selectedGene.aliases.join(', ')}</div>
            )}
            {selectedGene.description && (
              <div><strong>Description:</strong> {selectedGene.description}</div>
            )}
            {selectedGene.pathways && (
              <div><strong>Pathways:</strong> {selectedGene.pathways.join(', ')}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneSearch;