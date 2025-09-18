# 🔥 WildfireNowcast Frontend

A professional React-based showcase for the WildfireNowcast Agent's AI-powered wildfire monitoring and emergency response capabilities.

## 🎯 Overview

This frontend demonstrates the intelligent capabilities of the WildfireNowcast Agent through an interactive, professional interface. Instead of showing raw API calls, it showcases the agent's AI-powered analysis, decision-making process, and emergency response recommendations.

## ✨ Features

### 🤖 Agent Intelligence Showcase
- **Interactive Agent Conversation**: Chat with the agent and see intelligent responses
- **Real-time Agent Thinking**: Watch the agent analyze data step-by-step
- **AI Capabilities Display**: Shows all the agent's tools and capabilities
- **Live Insights**: Real-time AI-generated insights and recommendations
- **Performance Metrics**: Agent accuracy, response time, and monitoring status

### 🧠 Advanced Intelligence Components
- **Step-by-Step Analysis**: Visualizes the agent's thinking process
- **Threat Assessment Results**: Shows confidence levels and data points
- **Tool Usage Tracking**: Displays which AI tools the agent used
- **Recommendations Display**: AI-generated emergency response recommendations
- **Capabilities Overview**: Comprehensive view of all agent capabilities

### 📊 Traditional Data Dashboard
- **Interactive Charts**: Line charts, pie charts, and area charts
- **Fire Incident Table**: Searchable and filterable fire data
- **3D Earth Visualization**: Interactive globe showing fire locations
- **Weather Conditions**: Current environmental factors
- **Satellite Data**: NASA GIBS and EONET integration

### 🎨 User Experience
- **Dual View Mode**: Switch between Agent Showcase and Data Dashboard
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Theme**: Toggle between themes
- **Smooth Animations**: Professional transitions and interactions

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Recharts** for data visualization
- **Cobe** for 3D globe visualization
- **Radix UI** for accessible components
- **Lucide React** for icons

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** ([Download here](https://nodejs.org/))
- **Python 3.10+** (for the API server)
- **Your existing WildfireNowcast agent** (in the parent directory)

### Automated Setup (Recommended)

Run the automated setup script:

```bash
python setup.py
```

This will:
- ✅ Check prerequisites
- ✅ Install all dependencies
- ✅ Build the frontend
- ✅ Create startup scripts
- ✅ Set up the API server

### Manual Setup

If you prefer manual setup:

1. **Install frontend dependencies:**
   ```bash
   npm install
   ```

2. **Install backend API dependencies:**
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

3. **Create environment file:**
   ```bash
   echo "VITE_API_URL=http://localhost:8000" > .env
   ```

4. **Build the frontend:**
   ```bash
   npm run build
   ```

## 🎮 Running the Application

### Option 1: Full Stack (Recommended)

Start both frontend and backend together:
```bash
./start_full_stack.sh
```

### Option 2: Separate Components

**Terminal 1 - API Server:**
```bash
./start_api.sh
```

**Terminal 2 - Frontend:**
```bash
./start_dev.sh
```

### Option 3: Manual Start

```bash
# Start API server
python api_server.py

# Start frontend (in another terminal)
npm run dev
```

## 🌐 Access Points

Once running, you can access:

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                    # Reusable UI components
│   │   │   ├── card.tsx
│   │   │   ├── button.tsx
│   │   │   ├── chart.tsx
│   │   │   └── ...
│   │   ├── AgentShowcase.tsx      # Main agent showcase component
│   │   ├── AgentIntelligence.tsx  # Agent thinking visualization
│   │   └── WildfireDashboard.tsx  # Traditional data dashboard
│   ├── services/
│   │   └── api.ts                 # API integration service
│   ├── lib/
│   │   └── utils.ts               # Utility functions
│   ├── App.tsx                    # Main app component
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── api_server.py                  # FastAPI backend server
├── setup.py                       # Automated setup script
├── demo_agent.py                  # Agent capabilities demo
├── start_full_stack.sh            # Full stack startup script
├── start_dev.sh                   # Frontend development script
├── start_api.sh                   # API server script
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Key Components

### AgentShowcase
The main agent showcase component featuring:
- Interactive agent conversation interface
- Real-time agent thinking process visualization
- AI capabilities demonstration
- Live insights and recommendations
- Agent performance metrics
- Tool usage tracking

### AgentIntelligence
Advanced agent intelligence component featuring:
- Step-by-step thinking process
- Real-time analysis visualization
- Threat assessment results
- Confidence metrics and data points
- AI recommendations display
- Capabilities overview

### WildfireDashboard
Traditional data dashboard component featuring:
- Status cards with key metrics
- Interactive charts and graphs
- Fire incident table with filtering
- 3D Earth visualization
- Weather conditions panel
- Satellite data display
- Detailed fire information modal

### API Service
Integration with the WildfireNowcast backend:
- NASA FIRMS hotspot data
- GIBS satellite imagery
- EONET event data
- Threat assessment
- Fire mapping
- ICS reporting

### UI Components
Reusable components built with Radix UI:
- Cards, buttons, inputs
- Tables with sorting/filtering
- Charts with tooltips
- Progress bars and badges
- Tabs and separators

## Data Visualization

### Charts
- **Line Charts**: Fire activity trends over time
- **Pie Charts**: Fire severity distribution
- **Area Charts**: Temperature patterns
- **Progress Bars**: Containment percentages

### 3D Globe
- Interactive Earth visualization
- Fire location markers
- Size-based severity indicators
- Smooth rotation animation

## Styling

The project uses Tailwind CSS with:
- Custom color scheme for wildfire theme
- Dark/light mode support
- Responsive design utilities
- Custom animations and transitions

## API Integration

The frontend integrates with your WildfireNowcast backend through:

1. **NASA Data Endpoints**:
   - `/api/firms-hotspots` - FIRMS fire detection data
   - `/api/gibs-map-image` - Satellite imagery
   - `/api/eonet-events` - Event tracking

2. **Analysis Endpoints**:
   - `/api/threat-assessment` - Threat analysis
   - `/api/fire-map` - Map generation
   - `/api/ics-report` - Emergency reporting

3. **Agent Integration**:
   - `/api/agent-query` - Direct agent queries

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Adding New Features

1. **New Charts**: Add to the `TabsContent` in `WildfireDashboard.tsx`
2. **New API Endpoints**: Extend the `WildfireAPI` class in `api.ts`
3. **New UI Components**: Create in `components/ui/`
4. **New Data Types**: Add interfaces in `api.ts`

## Deployment

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Deploy to Static Hosting

The frontend can be deployed to:
- **Vercel**: Connect your GitHub repository
- **Netlify**: Drag and drop the `dist/` folder
- **AWS S3**: Upload the `dist/` contents
- **GitHub Pages**: Use the `gh-pages` package

### Environment Configuration

For production, set:
```env
VITE_API_URL=https://your-backend-api.com
```

## 🎭 Agent Demo

Run the agent capabilities demo:

```bash
python demo_agent.py
```

This demonstrates the agent's intelligent capabilities that are showcased in the frontend.

## 🎯 Usage Guide

### Agent Showcase Mode (Default)

1. **Interactive Chat**: Ask the agent questions about wildfire monitoring
2. **Agent Thinking**: Click "Start Analysis" to see the agent's thinking process
3. **Capabilities**: Explore the agent's AI tools and capabilities
4. **Insights**: View real-time AI-generated insights and recommendations

### Data Dashboard Mode

1. **Switch Views**: Use the toggle in the top-left to switch to "Data Dashboard"
2. **Charts**: Explore interactive charts and graphs
3. **Fire Table**: Search and filter fire incidents
4. **3D Globe**: Interact with the 3D Earth visualization

### Example Queries

Try these example queries in the Agent Showcase:

- "Check for wildfire hotspots in California"
- "Assess threats to critical infrastructure near current fires"
- "Generate a live map of current fire activity"
- "Draft an ICS situation report for current fires"
- "Recommend resource deployment for active incidents"
- "Calculate evacuation zones for active fires"

## 🆘 Troubleshooting

### Common Issues

**1. Node.js not found**
```bash
# Install Node.js from https://nodejs.org/
```

**2. npm install fails**
```bash
# Clear npm cache
npm cache clean --force
# Try again
npm install
```

**3. Port already in use**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**4. API connection errors**
```bash
# Check if API server is running
curl http://localhost:8000/health
# Check environment variables
cat .env
```

**5. Agent not found**
```bash
# Make sure you're running from the frontend directory
# and the parent directory contains your WildfireNowcast agent
ls ../wildfire_nowcast_agent.py
```

## 🎉 Success!

Once everything is running, you'll have a professional wildfire monitoring showcase that:

- ✅ **Showcases agent intelligence** and AI capabilities
- ✅ **Provides interactive experience** with the agent
- ✅ **Demonstrates professional emergency response** tools
- ✅ **Displays real-time NASA wildfire data**
- ✅ **Shows interactive 3D Earth visualization**
- ✅ **Works on all devices**
- ✅ **Integrates with your existing agent**
- ✅ **Looks professional and modern**

Enjoy your new WildfireNowcast Frontend! 🔥🤖🌍

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
