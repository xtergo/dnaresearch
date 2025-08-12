import axios from 'axios';

class AuthService {
  constructor() {
    this.token = localStorage.getItem('token');
    this.user = null;
    
    // Set up axios interceptor for authentication
    axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Handle 401 responses
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.logout();
        }
        return Promise.reject(error);
      }
    );
  }

  async login(username, password) {
    try {
      const response = await axios.post('http://localhost:7777/auth/login-json', {
        username,
        password
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      this.token = access_token;
      
      // Get user info
      const userResponse = await axios.get('http://localhost:7777/auth/me');
      this.user = userResponse.data;
      
      return { user: this.user, token: access_token };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  }

  async getCurrentUser() {
    if (!this.token) {
      return null;
    }
    
    try {
      const response = await axios.get('http://localhost:7777/auth/me');
      this.user = response.data;
      return this.user;
    } catch (error) {
      this.logout();
      return null;
    }
  }

  logout() {
    localStorage.removeItem('token');
    this.token = null;
    this.user = null;
    window.location.reload();
  }

  isAuthenticated() {
    return !!this.token;
  }

  getUser() {
    return this.user;
  }

  getToken() {
    return this.token;
  }

  hasRole(role) {
    return this.user?.role === role;
  }

  canAccess(requiredRole) {
    if (!this.user) return false;
    
    const roleHierarchy = {
      'user': 1,
      'researcher': 2,
      'admin': 3
    };
    
    const userLevel = roleHierarchy[this.user.role] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;
    
    return userLevel >= requiredLevel;
  }
}

export default new AuthService();