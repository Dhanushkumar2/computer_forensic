# ForensicIR Dashboard - React Frontend

An interactive forensic investigation dashboard built with React.js, featuring a warm color palette extracted from forensic imagery, smooth animations, and seamless Django backend integration.

## 🎨 Color Palette

The dashboard uses a carefully crafted color scheme inspired by forensic investigation themes:

- **Primary**: Warm browns (#8B6F47) - Professional and trustworthy
- **Secondary**: Sandy beige (#C4A57B) - Calm and analytical
- **Accents**: Warm highlights, cool blues, and status colors
- **Background**: Light cream tones for reduced eye strain

## ✨ Features

- **Multi-page Navigation**: Dashboard, Cases, Artifacts, Timeline, Analytics, Reports, Settings
- **Smooth Animations**: Framer Motion for fluid transitions and interactions
- **Responsive Design**: Mobile-first approach with Material-UI
- **Real-time Data**: Live updates from Django REST API
- **Interactive Charts**: Chart.js and Recharts for data visualization
- **Dark/Light Themes**: Customizable theme system

## 📦 Tech Stack

- **React 18.2** - UI framework
- **Material-UI 5** - Component library
- **Framer Motion** - Animation library
- **Chart.js & Recharts** - Data visualization
- **Axios** - HTTP client
- **React Router 6** - Navigation

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm/yarn
- Django backend running on port 8000

### Installation

```bash
# Navigate to frontend directory
cd forensic_ir_app/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Layout.js
│   │   │   ├── Sidebar.js
│   │   │   └── Header.js
│   │   └── Dashboard/
│   │       ├── StatCard.js
│   │       ├── ActivityChart.js
│   │       ├── ArtifactDistribution.js
│   │       └── CasesList.js
│   ├── pages/
│   │   ├── Dashboard/
│   │   ├── Cases/
│   │   ├── Artifacts/
│   │   ├── Timeline/
│   │   ├── Analytics/
│   │   ├── Reports/
│   │   └── Settings/
│   ├── services/
│   │   └── api.js
│   ├── theme/
│   │   ├── colors.js
│   │   └── theme.js
│   ├── App.js
│   ├── index.js
│   └── index.css
└── package.json
```

## 🎯 Pages

### Dashboard
- Overview statistics
- Activity charts
- Recent cases
- Artifact distribution

### Cases
- Case management
- Search and filter
- Status tracking
- Case details view

### Artifacts
- Artifact browser
- Advanced search
- Category filtering
- Detailed views

### Timeline
- Event timeline
- Interactive visualization
- Time-based filtering
- Export capabilities

### Analytics
- Statistical analysis
- Anomaly detection
- Pattern recognition
- Custom reports

### Reports
- Report generation
- Multiple formats (PDF, CSV, JSON)
- Template management
- Scheduled reports

## 🔌 API Integration

The frontend connects to Django backend via REST API:

```javascript
// Example API call
import { forensicAPI } from './services/api';

// Get dashboard stats
const stats = await forensicAPI.getDashboardStats();

// Get case details
const caseData = await forensicAPI.getCase(caseId);

// Search artifacts
const results = await forensicAPI.searchArtifacts(query);
```

## 🎨 Customization

### Colors

Edit `src/theme/colors.js` to customize the color palette:

```javascript
export const colors = {
  primary: {
    main: '#8B6F47',
    light: '#A68A64',
    dark: '#6B5437',
  },
  // ... more colors
};
```

### Theme

Modify `src/theme/theme.js` for typography, spacing, and component styles.

## 🔧 Environment Variables

Create `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
```

## 📊 Charts & Visualizations

The dashboard includes:

- **Line Charts**: Activity trends over time
- **Doughnut Charts**: Artifact distribution
- **Bar Charts**: Comparative analysis
- **Timeline Views**: Event sequences
- **Heatmaps**: Pattern visualization

## 🎭 Animations

Smooth animations powered by Framer Motion:

- Page transitions
- Card hover effects
- List item animations
- Loading states
- Micro-interactions

## 🔐 Authentication

The app includes authentication flow:

1. Login page with JWT token
2. Token storage in localStorage
3. Automatic token refresh
4. Protected routes
5. Logout functionality

## 📱 Responsive Design

Breakpoints:
- Mobile: < 600px
- Tablet: 600px - 960px
- Desktop: > 960px

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## 🚀 Deployment

### Build

```bash
npm run build
```

### Serve with Django

Copy build files to Django static directory:

```bash
cp -r build/* ../backend/static/
```

### Deploy to Production

1. Build the app
2. Configure Django to serve static files
3. Set up HTTPS
4. Configure CORS
5. Set environment variables

## 📝 Development Tips

1. **Hot Reload**: Changes auto-refresh in development
2. **DevTools**: React DevTools for debugging
3. **API Proxy**: Configured in package.json
4. **Linting**: ESLint for code quality
5. **Formatting**: Prettier for consistent style

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## 📄 License

This project is part of the ForensicIR investigation platform.

## 🆘 Support

For issues or questions:
- Check documentation
- Review API endpoints
- Check browser console
- Verify backend connection

## 🎓 Learning Resources

- [React Documentation](https://react.dev/)
- [Material-UI Docs](https://mui.com/)
- [Framer Motion Guide](https://www.framer.com/motion/)
- [Chart.js Docs](https://www.chartjs.org/)

---

Built with ❤️ for digital forensics professionals
