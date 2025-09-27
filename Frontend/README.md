# AlertMate Frontend

A React-based frontend for the AlertMate Emergency Response System.

## Features

- **Authentication System**: User login and signup with session management
- **Emergency Chat Interface**: Real-time chat with emergency services
- **Admin Dashboard**: Administrative interface for monitoring system status
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Updates**: Auto-refreshing data and live status indicators

## Technology Stack

- **React 19** - Modern React with hooks and functional components
- **React Router DOM** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication
- **Vite** - Fast development server and build tool

## Project Structure

```
src/
├── components/
│   ├── AuthPage.jsx          # Login/Signup page
│   ├── ChatPage.jsx          # Emergency chat interface
│   ├── AdminPage.jsx         # Admin dashboard
│   └── ProtectedRoute.jsx    # Route protection wrapper
├── contexts/
│   └── AuthContext.jsx       # Authentication state management
├── services/
│   └── api.js                # API service layer
├── App.jsx                   # Main app component with routing
├── main.jsx                  # Application entry point
└── index.css                 # Global styles
```

## Getting Started

### Prerequisites

- Node.js 16+ installed
- Backend server running on http://127.0.0.1:8000

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd Frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser to http://localhost:5173

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## API Integration

The frontend communicates with the backend API at `http://127.0.0.1:8000/api/v1`. Key endpoints:

- `POST /auth/login` - User authentication
- `POST /auth/signup` - User registration
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user
- `POST /chat` - Send emergency messages
- `GET /admin/stats` - Admin statistics
- `GET /admin/queue` - Active emergency queue
- `GET /admin/activity` - Recent activity log

## Components Overview

### AuthPage
- Handles both login and signup
- Form validation and error handling
- Geolocation support for user registration
- CNIC formatting for Pakistani users
- Automatic redirect after successful authentication

### ChatPage
- Emergency chat interface
- Quick action buttons for common emergencies
- Real-time message display
- User location and emergency hotlines
- Support for English, Urdu, and Roman Urdu

### AdminPage
- Real-time dashboard with key metrics
- Active emergency queue monitoring
- Recent activity feed
- Service distribution charts
- Auto-refresh every 30 seconds

### ProtectedRoute
- Route guard for authenticated pages
- Loading states during authentication checks
- Automatic redirect to login for unauthenticated users

## Authentication Flow

1. User visits the app
2. If not authenticated, redirected to `/auth`
3. User can login with existing credentials or signup
4. Upon successful authentication, redirected to `/chat`
5. Session is maintained via HTTP-only cookies
6. Admin users can access `/admin` dashboard

## Styling

The app uses Tailwind CSS with a dark theme and glassmorphism design:

- **Colors**: Slate color palette with blue accents
- **Components**: Glass-effect cards with backdrop blur
- **Animations**: Smooth transitions and loading spinners
- **Responsive**: Mobile-first responsive design

## Security

- HTTP-only cookies for session management
- CORS configured for localhost development
- Input validation on all forms
- Protected routes with authentication guards
- Secure API communication with credentials

## Development Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Browser Support

- Modern browsers with ES2020+ support
- Chrome 87+
- Firefox 78+
- Safari 14+
- Edge 88++ Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
