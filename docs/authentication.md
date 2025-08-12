# Authentication System

The DNA Research Platform now includes a basic JWT-based authentication system for the MVP.

## Features

- **JWT Token Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Three user roles (user, researcher, admin)
- **Test Accounts**: Pre-configured test accounts for development
- **Protected Endpoints**: Theory creation/management requires authentication
- **Frontend Integration**: React components with login/logout functionality

## Test Accounts

For development and testing, the following accounts are available:

| Username   | Password     | Role       | Description                    |
|------------|--------------|------------|--------------------------------|
| admin      | admin123     | admin      | Full system access             |
| researcher | research123  | researcher | Research and theory management |
| user       | user123      | user       | Basic platform access          |

## API Endpoints

### Authentication Endpoints

- `POST /auth/login-json` - Login with username/password
- `GET /auth/me` - Get current user information
- `POST /auth/register` - Register new user
- `GET /auth/users` - List users (admin only)
- `GET /auth/test-users` - Get test account credentials

### Protected Endpoints

The following endpoints now require authentication:

- `POST /theories` - Create theory
- `PUT /theories/{theory_id}` - Update theory
- `DELETE /theories/{theory_id}` - Delete theory

## Frontend Usage

### Login Component

The React frontend includes a login component with:
- Username/password form
- Quick login buttons for test accounts
- Error handling and loading states
- Automatic token storage

### Authentication Service

The `authService` provides:
- Login/logout functionality
- Token management
- Role-based access checks
- Automatic API request authentication

## Configuration

### Environment Variables

- `JWT_SECRET_KEY`: Secret key for JWT token signing (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30 minutes)

### Development

```bash
# Development JWT secret (change in production)
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
```

### Production

```bash
# Production JWT secret (use a secure random key)
JWT_SECRET_KEY=your-secure-jwt-secret-key-at-least-32-characters
```

## Security Notes

⚠️ **Important for Production:**

1. **Change JWT Secret**: Use a secure random key in production
2. **HTTPS Only**: Always use HTTPS in production
3. **Token Expiration**: Consider shorter token expiration times
4. **User Management**: Replace mock user database with real database
5. **Password Policy**: Implement strong password requirements
6. **Rate Limiting**: Add rate limiting to login endpoints

## Testing

Run authentication tests:

```bash
cd api
python -m pytest test_auth.py -v
```

## Usage Examples

### Login via API

```bash
curl -X POST "http://localhost:8000/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Access Protected Endpoint

```bash
curl -X POST "http://localhost:8000/theories" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "test-theory", "version": "1.0.0", "scope": "autism"}'
```

### Frontend Login

```javascript
import authService from './services/auth';

// Login
const { user, token } = await authService.login('admin', 'admin123');

// Check if authenticated
if (authService.isAuthenticated()) {
  // User is logged in
}

// Logout
authService.logout();
```

## Next Steps

For a production deployment, consider:

1. **Database Integration**: Store users in PostgreSQL
2. **OAuth Integration**: Add Google/GitHub OAuth
3. **Password Reset**: Email-based password reset
4. **Session Management**: Redis-based session storage
5. **Audit Logging**: Track authentication events
6. **Multi-Factor Authentication**: Add 2FA support