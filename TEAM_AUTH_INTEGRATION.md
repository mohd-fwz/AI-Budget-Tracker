# Team Authentication Integration Guide

## The Problem

We have multiple microservices built by different team members, each with their own authentication:
- Each service is hosted separately
- Users shouldn't have to login to each service individually
- Main dashboard needs to provide unified access to all services

## The Solution: Shared JWT Authentication

All services trust a **single JWT token** issued by the main dashboard. When a user logs into the dashboard, they receive a token that works across ALL team services.

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN DASHBOARD                            │
│                   (Authentication Hub)                       │
│                                                             │
│   User logs in once → Receives JWT token                    │
│                                                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Same JWT token passed to all services
                      │
    ┌─────────────────┼─────────────────┬─────────────────┐
    ▼                 ▼                 ▼                 ▼
┌────────┐      ┌────────┐       ┌────────┐       ┌────────┐
│ Budget │      │Service │       │Service │       │Service │
│  App   │      │   B    │       │   C    │       │   D    │
│(Python)│      │ (JS)   │       │(Python)│       │ (JS)   │
└────────┘      └────────┘       └────────┘       └────────┘
     │               │                │                │
     └───────────────┴────────────────┴────────────────┘
                    All validate same JWT secret
```

---

## Setup Instructions

### Step 1: Generate Shared Secret (Team Lead does this ONCE)

```bash
# Generate a secure 64-byte secret
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"

# Or with Python
python -c "import secrets; print(secrets.token_hex(64))"
```

**Share this secret securely with all team members** (use a password manager, not chat).

### Step 2: Environment Variable (ALL team members)

Add to your `.env` file:

```bash
DASHBOARD_JWT_SECRET=<the-shared-secret-from-team-lead>
```

### Step 3: Install JWT Library

**Python backends:**
```bash
pip install PyJWT
```

**Node.js backends:**
```bash
npm install jsonwebtoken
```

---

## Code Implementation

### For Python/Flask Services

Create `shared_auth.py` in your project:

```python
"""
Shared Authentication Module
Validates JWT tokens issued by the main dashboard
"""
import os
import jwt
from functools import wraps
from flask import request, jsonify, g

# Shared secret - MUST match all services
SHARED_JWT_SECRET = os.getenv('DASHBOARD_JWT_SECRET')
JWT_ALGORITHM = 'HS256'


def verify_dashboard_token():
    """
    Verify JWT token from main dashboard

    Returns:
        tuple: (payload_dict, error_string)
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None, 'No token provided'

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(
            token,
            SHARED_JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except jwt.InvalidTokenError as e:
        return None, f'Invalid token: {str(e)}'


def require_dashboard_auth(f):
    """
    Decorator for routes that require dashboard authentication

    Usage:
        @app.route('/api/protected')
        @require_dashboard_auth
        def protected_route():
            user_id = g.user_id  # Access user info
            return jsonify({'message': f'Hello {g.user_email}'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        payload, error = verify_dashboard_token()

        if error:
            return jsonify({
                'error': 'Unauthorized',
                'message': error
            }), 401

        # Attach user info to Flask's g object
        g.user_id = payload.get('user_id')
        g.user_email = payload.get('email')
        g.user_name = payload.get('name')

        return f(*args, **kwargs)
    return decorated
```

**Usage in your routes:**

```python
from shared_auth import require_dashboard_auth

@app.route('/api/your-feature', methods=['GET'])
@require_dashboard_auth
def your_feature():
    # User info is available via g
    user_id = g.user_id

    # Your feature logic here
    return jsonify({'success': True, 'user': g.user_email})
```

---

### For Node.js/Express Services

Create `shared-auth.js` in your project:

```javascript
/**
 * Shared Authentication Module
 * Validates JWT tokens issued by the main dashboard
 */
const jwt = require('jsonwebtoken');

// Shared secret - MUST match all services
const SHARED_JWT_SECRET = process.env.DASHBOARD_JWT_SECRET;

/**
 * Express middleware to verify dashboard JWT token
 *
 * Usage:
 *   app.get('/api/protected', requireDashboardAuth, (req, res) => {
 *     const userId = req.user.userId;
 *     res.json({ message: `Hello ${req.user.email}` });
 *   });
 */
const requireDashboardAuth = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'No token provided'
    });
  }

  const token = authHeader.split(' ')[1];

  try {
    const payload = jwt.verify(token, SHARED_JWT_SECRET);

    // Attach user info to request object
    req.user = {
      userId: payload.user_id,
      email: payload.email,
      name: payload.name
    };

    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Token expired'
      });
    }
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid token'
    });
  }
};

module.exports = { requireDashboardAuth };
```

**Usage in your routes:**

```javascript
const { requireDashboardAuth } = require('./shared-auth');

app.get('/api/your-feature', requireDashboardAuth, (req, res) => {
  // User info is available via req.user
  const userId = req.user.userId;

  // Your feature logic here
  res.json({ success: true, user: req.user.email });
});
```

---

## Main Dashboard: Token Issuance

The main dashboard (authentication hub) needs to issue tokens that all services accept.

### Python Dashboard

```python
import os
import jwt
from datetime import datetime, timedelta

SHARED_JWT_SECRET = os.getenv('DASHBOARD_JWT_SECRET')

def create_shared_token(user):
    """
    Create JWT token accepted by all team services

    Args:
        user: User object with id, email, name attributes

    Returns:
        str: JWT token string
    """
    payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }

    return jwt.encode(payload, SHARED_JWT_SECRET, algorithm='HS256')


# In your login route:
@app.route('/api/auth/login', methods=['POST'])
def login():
    # ... validate credentials ...

    token = create_shared_token(user)

    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name
        }
    })
```

### Node.js Dashboard

```javascript
const jwt = require('jsonwebtoken');

const SHARED_JWT_SECRET = process.env.DASHBOARD_JWT_SECRET;

/**
 * Create JWT token accepted by all team services
 */
function createSharedToken(user) {
  const payload = {
    user_id: user.id,        // Use snake_case for cross-language compatibility
    email: user.email,
    name: user.name,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60)  // 24 hours
  };

  return jwt.sign(payload, SHARED_JWT_SECRET, { algorithm: 'HS256' });
}

// In your login route:
app.post('/api/auth/login', async (req, res) => {
  // ... validate credentials ...

  const token = createSharedToken(user);

  res.json({
    success: true,
    token: token,
    user: {
      id: user.id,
      email: user.email,
      name: user.name
    }
  });
});

module.exports = { createSharedToken };
```

---

## Frontend: Using the Token

The frontend stores the token once and passes it to ALL team services.

```javascript
// After login, store the token
const login = async (email, password) => {
  const response = await fetch('https://dashboard.yourteam.com/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();

  if (data.success) {
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }

  return data;
};

// Helper to call ANY team service
const callService = async (serviceBaseUrl, endpoint, options = {}) => {
  const token = localStorage.getItem('auth_token');

  const response = await fetch(`${serviceBaseUrl}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,  // Same token for ALL services
      ...options.headers
    }
  });

  // Handle token expiration
  if (response.status === 401) {
    localStorage.removeItem('auth_token');
    window.location.href = '/login';
    return null;
  }

  return response.json();
};

// Usage examples:
await callService('https://budget.yourteam.com', '/api/expenses');
await callService('https://inventory.yourteam.com', '/api/items');
await callService('https://analytics.yourteam.com', '/api/reports');
```

---

## Service URLs Configuration

Create a config file for all service URLs:

```javascript
// services.config.js
const SERVICES = {
  dashboard: process.env.REACT_APP_DASHBOARD_URL || 'http://localhost:3000',
  budget: process.env.REACT_APP_BUDGET_URL || 'http://localhost:5000',
  inventory: process.env.REACT_APP_INVENTORY_URL || 'http://localhost:5001',
  analytics: process.env.REACT_APP_ANALYTICS_URL || 'http://localhost:5002',
  // Add more services as needed
};

export default SERVICES;
```

---

## Quick Reference

| Task | Python | Node.js |
|------|--------|---------|
| Install JWT | `pip install PyJWT` | `npm install jsonwebtoken` |
| Env variable | `DASHBOARD_JWT_SECRET` | `DASHBOARD_JWT_SECRET` |
| Auth file | `shared_auth.py` | `shared-auth.js` |
| Decorator/Middleware | `@require_dashboard_auth` | `requireDashboardAuth` |
| Access user ID | `g.user_id` | `req.user.userId` |
| Access email | `g.user_email` | `req.user.email` |

---

## Security Checklist

- [ ] JWT secret is at least 64 characters
- [ ] Secret is stored in environment variables, NOT in code
- [ ] Secret is shared securely (password manager, NOT chat/email)
- [ ] All services use HTTPS in production
- [ ] Token expiration is set (recommended: 24 hours)
- [ ] Frontend handles 401 responses (redirect to login)

---

## Troubleshooting

### "Invalid token" error
- Check that ALL services have the exact same `DASHBOARD_JWT_SECRET`
- Verify the token hasn't been modified in transit
- Check the algorithm matches (`HS256`)

### "Token expired" error
- User needs to login again
- Consider implementing token refresh

### Token not being sent
- Check frontend is including `Authorization: Bearer <token>` header
- Verify CORS is configured to allow the Authorization header

### User info not available
- Python: Make sure to use `g.user_id`, not `request.user_id`
- Node.js: Make sure to use `req.user.userId`, not `req.userId`

---

## Future Improvements

1. **Token Refresh**: Implement refresh tokens for better UX
2. **Role-Based Access**: Add roles to JWT payload for authorization
3. **Service-to-Service Auth**: For backend services that need to call each other
4. **Centralized User Store**: Share user data across services via API

---

## Questions?

Contact the team lead or refer to the project documentation.
