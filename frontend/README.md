# FloatChat Frontend

A modern React + Vite frontend for the FloatChat ARGO Ocean Data Assistant.

## Features

- 🌊 Interactive map interface with ARGO float locations
- 💬 Natural language chat interface for data queries
- 📊 Real-time data visualizations and charts
- 📱 Responsive design for all devices
- 🔍 Advanced search and filtering capabilities
- 📥 Data export functionality

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx      # Main dashboard component
│   │   ├── ChatInput.jsx      # Chat input component
│   │   └── VisualizationPanel.jsx # Data visualization panel
│   ├── App.jsx                # Root app component
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles
├── public/                   # Static assets
├── package.json             # Dependencies and scripts
└── vite.config.js          # Vite configuration
```

## API Integration

The frontend connects to the FastAPI backend running on `http://localhost:8000`. Make sure the backend is running before starting the frontend.

### Available Endpoints

- `POST /api/chat` - Send chat queries
- `GET /api/data` - Fetch data directly

## Technologies Used

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Leaflet** - Interactive maps
- **Plotly.js** - Data visualizations
- **React Markdown** - Markdown rendering
- **Lucide React** - Icons
- **CSS3** - Styling with modern features

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_URL=http://localhost:8000
```

## Deployment

The frontend can be deployed to any static hosting service:

- **Vercel**: Connect your GitHub repository
- **Netlify**: Drag and drop the `dist` folder
- **AWS S3**: Upload the `dist` folder contents
- **Docker**: Use the provided Dockerfile

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is part of the FloatChat system built for MoES/INCOIS.
