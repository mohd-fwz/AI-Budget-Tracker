# Budget Tracker Frontend

Modern React frontend for the Budget API with beautiful UI, real-time analytics, and AI-powered insights.

## Features

- 🔐 **Secure Authentication** - Supabase Auth with JWT tokens
- 💰 **Expense Management** - Add, view, filter, and delete expenses
- 📊 **Visual Analytics** - Interactive charts and spending trends
- 📤 **CSV Upload** - Import bank statements automatically
- 🤖 **AI Recommendations** - Personalized savings tips from AI
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎨 **Modern UI** - Built with Tailwind CSS and Lucide icons

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **Charts**: Recharts
- **Icons**: Lucide React
- **Auth**: Supabase
- **HTTP Client**: Axios
- **Date Utilities**: date-fns

## Project Structure

```
budget-frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx          # Main dashboard layout
│   │   ├── ExpensesView.jsx       # Expense management
│   │   ├── AnalyticsView.jsx      # Analytics dashboard
│   │   ├── UploadView.jsx         # CSV upload interface
│   │   └── RecommendationsView.jsx # AI tips display
│   ├── pages/
│   │   ├── Login.jsx              # Login page
│   │   └── SignUp.jsx             # Sign up page
│   ├── contexts/
│   │   └── AuthContext.jsx        # Authentication state
│   ├── services/
│   │   └── api.js                 # API calls
│   ├── utils/
│   │   └── supabase.js            # Supabase client
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles
├── public/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## Quick Start

### Prerequisites

- Node.js 16+ and npm
- Running Budget API backend
- Supabase account

### Installation

1. **Install dependencies**
   ```bash
   cd budget-frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   VITE_API_URL=http://localhost:5000
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

   App will open at `http://localhost:3000`

## Environment Variables

Create a `.env` file with these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_SUPABASE_URL` | Your Supabase project URL | `https://xxx.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJhbG...` |
| `VITE_API_URL` | Backend API URL | `http://localhost:5000` |

**Note**: All environment variables must be prefixed with `VITE_` to be accessible in the frontend.

## Usage

### Authentication

1. **Sign Up**
   - Navigate to `/signup`
   - Enter email and password
   - Account created automatically

2. **Sign In**
   - Navigate to `/login`
   - Enter credentials
   - Redirects to dashboard on success

### Managing Expenses

1. **Add Expense**
   - Click "Add Expense" button
   - Fill in amount (required)
   - Optional: Select category (auto-detected if blank)
   - Optional: Set date (defaults to today)
   - Optional: Add description
   - Click "Add Expense"

2. **View Expenses**
   - See all expenses in a table
   - Filter by category using dropdown
   - View total at bottom

3. **Delete Expense**
   - Click trash icon next to expense
   - Confirm deletion

### Analytics

- View spending by category (pie chart)
- See spending trends over time (bar chart)
- Check summary statistics (total, average, count)
- Review top expenses
- Switch between daily/weekly/monthly views

### CSV Upload

1. Click "Upload CSV" tab
2. Select CSV file from your bank
3. Click "Upload and Import"
4. View import results (imported, skipped, total)

**CSV Format Requirements:**
- Must have Date, Description, and Amount columns
- Date format: YYYY-MM-DD, MM/DD/YYYY, or similar
- Amount: Numeric value (with or without $, commas)

### AI Recommendations

- View personalized savings tips
- See spending summary
- Get category-specific advice
- Select time period (7, 30, or 90 days)

## Component Overview

### Dashboard.jsx
Main layout with navigation sidebar and content area. Handles view switching.

### ExpensesView.jsx
Complete expense management:
- Add expense form
- Expense list table
- Category filter
- Delete functionality

### AnalyticsView.jsx
Visual analytics dashboard:
- Summary cards (total, count, average)
- Pie chart (category breakdown)
- Bar chart (spending trends)
- Category breakdown table
- Top expenses list

### UploadView.jsx
CSV upload interface:
- File selection
- Upload progress
- Success/error feedback
- Format instructions

### RecommendationsView.jsx
AI-powered savings tips:
- Spending summary cards
- AI recommendations list
- Quick insights
- Time period selector

## Styling

### Tailwind CSS

The app uses Tailwind CSS for styling:

```jsx
// Example: Primary button
<button className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
  Click Me
</button>
```

### Custom Colors

Defined in `tailwind.config.js`:
- Primary: Blue shades (#0ea5e9 and variants)
- Custom colors for categories

### Responsive Design

Uses Tailwind's responsive prefixes:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
  {/* 1 column on mobile, 2 on tablet, 4 on desktop */}
</div>
```

## API Integration

### Service Layer

All API calls are centralized in `src/services/api.js`:

```javascript
import { expenseAPI, analyticsAPI, recommendationsAPI } from './services/api'

// Add expense
await expenseAPI.addExpense({ amount: 50, description: 'Groceries' })

// Get expenses
const data = await expenseAPI.getExpenses(userId, { category: 'Groceries' })

// Get analytics
const analytics = await analyticsAPI.getAnalytics(userId, { period: 'monthly' })
```

### Authentication

Automatic token injection via Axios interceptor:
- Gets current session from Supabase
- Adds `Authorization: Bearer <token>` header
- Handles 401 errors (redirects to login)

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Connect repository to Vercel
3. Configure environment variables
4. Deploy automatically

### Netlify

1. Build the app: `npm run build`
2. Deploy `dist` folder to Netlify
3. Configure environment variables
4. Set build command: `npm run build`
5. Set publish directory: `dist`

### Manual Deployment

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Deploy dist/ folder to your hosting
```

## Development

### Adding a New Component

1. Create component file in `src/components/`
2. Use functional component with hooks
3. Follow existing naming conventions
4. Export as default

Example:
```jsx
import { useState } from 'react'

export default function MyComponent() {
  const [state, setState] = useState('')

  return (
    <div className="p-6">
      {/* Component content */}
    </div>
  )
}
```

### State Management

Uses React Context for global state:
- `AuthContext`: User authentication state
- Component-level state with `useState`
- API calls with `useEffect`

### Routing

Protected routes in `App.jsx`:
```jsx
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

## Testing

### Manual Testing Checklist

- [ ] Sign up new user
- [ ] Sign in existing user
- [ ] Add expense (with and without category)
- [ ] View expenses
- [ ] Filter expenses by category
- [ ] Delete expense
- [ ] View analytics dashboard
- [ ] Upload CSV file
- [ ] View AI recommendations
- [ ] Sign out

### Browser Compatibility

Tested on:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### CORS Errors

**Problem**: `Access to fetch blocked by CORS policy`

**Solution**:
- Update `CORS_ORIGINS` in backend `.env`
- Add your frontend URL: `http://localhost:3000`

### Authentication Issues

**Problem**: "Invalid or expired token"

**Solution**:
- Check `VITE_SUPABASE_JWT_SECRET` matches backend
- Clear browser storage and re-login
- Verify Supabase configuration

### API Connection Failed

**Problem**: Cannot connect to backend

**Solution**:
- Verify backend is running
- Check `VITE_API_URL` is correct
- Test backend health: `curl http://localhost:5000/health`

### Charts Not Displaying

**Problem**: Analytics charts are blank

**Solution**:
- Add some expenses first
- Check browser console for errors
- Verify analytics API returns data

## Performance Optimization

- Lazy loading for routes (can be added)
- React.memo for expensive components
- Debounced API calls
- Efficient re-renders with proper dependencies

## Security

- Environment variables for sensitive data
- HTTPS in production
- JWT tokens in memory only
- Auto-logout on token expiration
- XSS protection via React

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ features required
- No IE11 support

## License

MIT License - free to use in your projects

## Support

For issues or questions:
- Check backend API is running
- Review browser console for errors
- Verify environment variables
- Check network tab for failed requests

---

Built with ❤️ using React and Tailwind CSS
