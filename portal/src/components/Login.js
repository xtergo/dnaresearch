import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:7777/auth/login-json', credentials);
      const { access_token } = response.data;
      
      // Store token
      localStorage.setItem('token', access_token);
      
      // Get user info
      const userResponse = await axios.get('http://localhost:7777/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      
      onLogin(userResponse.data, access_token);
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed');
    }
    setIsLoading(false);
  };

  const handleTestLogin = async (username, password) => {
    setCredentials({ username, password });
    setIsLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:7777/auth/login-json', { username, password });
      const { access_token } = response.data;
      
      localStorage.setItem('token', access_token);
      
      const userResponse = await axios.get('http://localhost:7777/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      
      onLogin(userResponse.data, access_token);
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed');
    }
    setIsLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>🧬 DNA Research Platform</h2>
        <p>Please log in to continue</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              required
            />
          </div>
          
          <button type="submit" disabled={isLoading} className="btn btn-primary">
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <div className="test-accounts">
          <h4>Test Accounts</h4>
          <div className="test-buttons">
            <button 
              onClick={() => handleTestLogin('admin', 'admin123')}
              className="btn btn-secondary"
              disabled={isLoading}
            >
              Admin
            </button>
            <button 
              onClick={() => handleTestLogin('researcher', 'research123')}
              className="btn btn-secondary"
              disabled={isLoading}
            >
              Researcher
            </button>
            <button 
              onClick={() => handleTestLogin('user', 'user123')}
              className="btn btn-secondary"
              disabled={isLoading}
            >
              User
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;