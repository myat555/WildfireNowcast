import { useState } from 'react'
import { WildfireDashboard } from './components/WildfireDashboard'
import { AgentShowcase } from './components/AgentShowcase'
import { Button } from './components/ui/button'
import { Moon, Sun, Bot, BarChart3 } from 'lucide-react'

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [activeView, setActiveView] = useState<'agent' | 'dashboard'>('agent')

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode)
    document.documentElement.classList.toggle('dark')
  }

  return (
    <div className={isDarkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-background">
        {/* Theme Toggle */}
        <div className="fixed top-4 right-4 z-50">
          <Button
            variant="outline"
            size="icon"
            onClick={toggleDarkMode}
            className="bg-background/80 backdrop-blur-sm"
          >
            {isDarkMode ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* View Toggle */}
        <div className="fixed top-4 left-4 z-50">
          <div className="flex gap-2 bg-background/80 backdrop-blur-sm rounded-lg border p-1">
            <Button
              variant={activeView === 'agent' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveView('agent')}
              className="flex items-center gap-2"
            >
              <Bot className="h-4 w-4" />
              Agent Showcase
            </Button>
            <Button
              variant={activeView === 'dashboard' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveView('dashboard')}
              className="flex items-center gap-2"
            >
              <BarChart3 className="h-4 w-4" />
              Data Dashboard
            </Button>
          </div>
        </div>

        {/* Main Content */}
        {activeView === 'agent' ? <AgentShowcase /> : <WildfireDashboard />}
      </div>
    </div>
  )
}

export default App
