"use client"

import * as React from "react"
import { useState, useEffect, useRef, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Flame, 
  AlertTriangle, 
  Satellite, 
  Wind, 
  Thermometer, 
  Droplets,
  Eye,
  Activity,
  TrendingUp,
  TrendingDown,
  MapPin,
  Calendar,
  Clock,
  Filter,
  Search,
  Settings,
  Bell,
  Download,
  RefreshCw,
  Zap,
  Shield,
  Globe
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { 
  ChartContainer, 
  ChartTooltip, 
  ChartTooltipContent,
  ChartConfig
} from "@/components/ui/chart"
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts"
import createGlobe, { COBEOptions } from "cobe"

// Types
interface WildfireData {
  id: string
  name: string
  location: string
  coordinates: [number, number]
  severity: "low" | "moderate" | "high" | "extreme"
  size: number
  containment: number
  lastUpdated: string
  temperature: number
  humidity: number
  windSpeed: number
  windDirection: string
  threatLevel: number
  evacuationZones: string[]
  resources: {
    personnel: number
    aircraft: number
    groundVehicles: number
  }
}

interface WeatherData {
  temperature: number
  humidity: number
  windSpeed: number
  windDirection: string
  pressure: number
  visibility: number
}

interface ThreatAssessment {
  overall: number
  factors: {
    weather: number
    terrain: number
    vegetation: number
    proximity: number
  }
}

// Mock data
const mockWildfires: WildfireData[] = [
  {
    id: "WF001",
    name: "Canyon Fire",
    location: "Los Angeles County, CA",
    coordinates: [34.0522, -118.2437],
    severity: "extreme",
    size: 15420,
    containment: 25,
    lastUpdated: "2024-01-15T14:30:00Z",
    temperature: 95,
    humidity: 15,
    windSpeed: 35,
    windDirection: "NE",
    threatLevel: 9.2,
    evacuationZones: ["Zone A", "Zone B", "Zone C"],
    resources: {
      personnel: 450,
      aircraft: 12,
      groundVehicles: 85
    }
  },
  {
    id: "WF002",
    name: "Ridge Complex",
    location: "Riverside County, CA",
    coordinates: [33.7175, -116.2023],
    severity: "high",
    size: 8750,
    containment: 60,
    lastUpdated: "2024-01-15T14:25:00Z",
    temperature: 88,
    humidity: 22,
    windSpeed: 18,
    windDirection: "SW",
    threatLevel: 7.1,
    evacuationZones: ["Zone D"],
    resources: {
      personnel: 280,
      aircraft: 8,
      groundVehicles: 45
    }
  },
  {
    id: "WF003",
    name: "Valley Blaze",
    location: "Ventura County, CA",
    coordinates: [34.3705, -119.2293],
    severity: "moderate",
    size: 3200,
    containment: 80,
    lastUpdated: "2024-01-15T14:20:00Z",
    temperature: 82,
    humidity: 35,
    windSpeed: 12,
    windDirection: "W",
    threatLevel: 4.8,
    evacuationZones: [],
    resources: {
      personnel: 150,
      aircraft: 4,
      groundVehicles: 25
    }
  }
]

const chartData = [
  { time: "00:00", fires: 12, threats: 65, temperature: 75 },
  { time: "04:00", fires: 15, threats: 72, temperature: 78 },
  { time: "08:00", fires: 18, threats: 78, temperature: 85 },
  { time: "12:00", fires: 22, threats: 85, temperature: 92 },
  { time: "16:00", fires: 25, threats: 90, temperature: 95 },
  { time: "20:00", fires: 20, threats: 82, temperature: 88 }
]

const severityData = [
  { name: "Low", value: 35, color: "#22c55e" },
  { name: "Moderate", value: 25, color: "#eab308" },
  { name: "High", value: 30, color: "#f97316" },
  { name: "Extreme", value: 10, color: "#dc2626" }
]

const chartConfig: ChartConfig = {
  fires: {
    label: "Active Fires",
    color: "#dc2626"
  },
  threats: {
    label: "Threat Level",
    color: "#f97316"
  },
  temperature: {
    label: "Temperature",
    color: "#eab308"
  }
}

// Globe Component
function Globe3D({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [globe, setGlobe] = useState<any>(null)

  useEffect(() => {
    if (!canvasRef.current) return

    const globeInstance = createGlobe(canvasRef.current, {
      devicePixelRatio: 2,
      width: 400,
      height: 400,
      phi: 0,
      theta: 0.3,
      dark: 1,
      diffuse: 1.2,
      mapSamples: 16000,
      mapBrightness: 6,
      baseColor: [0.3, 0.3, 0.3],
      markerColor: [1, 0.2, 0.2],
      glowColor: [1, 1, 1],
      markers: mockWildfires.map(fire => ({
        location: fire.coordinates,
        size: fire.severity === "extreme" ? 0.08 : 
              fire.severity === "high" ? 0.06 :
              fire.severity === "moderate" ? 0.04 : 0.02
      })),
      onRender: (state) => {
        state.phi = state.phi + 0.005
      }
    })

    setGlobe(globeInstance)

    return () => {
      globeInstance.destroy()
    }
  }, [])

  return (
    <div className={className}>
      <canvas
        ref={canvasRef}
        style={{
          width: "100%",
          height: "100%",
          maxWidth: "400px",
          aspectRatio: "1"
        }}
      />
    </div>
  )
}

// Severity Badge Component
function SeverityBadge({ severity }: { severity: string }) {
  const variants = {
    low: "bg-green-100 text-green-800 border-green-200",
    moderate: "bg-yellow-100 text-yellow-800 border-yellow-200",
    high: "bg-orange-100 text-orange-800 border-orange-200",
    extreme: "bg-red-100 text-red-800 border-red-200"
  }

  return (
    <Badge className={variants[severity as keyof typeof variants]}>
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </Badge>
  )
}

// Main Dashboard Component
export function WildfireMonitoringDashboard() {
  const [selectedFire, setSelectedFire] = useState<WildfireData | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [severityFilter, setSeverityFilter] = useState("all")
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  const filteredFires = useMemo(() => {
    return mockWildfires.filter(fire => {
      const matchesSearch = fire.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           fire.location.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesSeverity = severityFilter === "all" || fire.severity === severityFilter
      return matchesSearch && matchesSeverity
    })
  }, [searchTerm, severityFilter])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setLastUpdate(new Date())
    setIsRefreshing(false)
  }

  const totalFires = mockWildfires.length
  const activeFires = mockWildfires.filter(f => f.containment < 100).length
  const extremeFires = mockWildfires.filter(f => f.severity === "extreme").length
  const avgContainment = Math.round(mockWildfires.reduce((acc, f) => acc + f.containment, 0) / totalFires)

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
              <Flame className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>
            Wildfire Monitoring Dashboard
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Real-time NASA wildfire data and threat assessment
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export
          </Button>
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Alerts
          </Button>
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Fires</CardTitle>
            <Flame className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{activeFires}</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {totalFires} total incidents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Extreme Threats</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{extremeFires}</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Requiring immediate attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Containment</CardTitle>
            <Shield className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{avgContainment}%</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Across all incidents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Update</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {lastUpdate.toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Charts and Analytics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Charts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Fire Activity Trends
              </CardTitle>
              <CardDescription>
                24-hour monitoring data showing fire count, threat levels, and temperature
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="timeline" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="timeline">Timeline</TabsTrigger>
                  <TabsTrigger value="severity">Severity</TabsTrigger>
                  <TabsTrigger value="temperature">Temperature</TabsTrigger>
                </TabsList>
                
                <TabsContent value="timeline" className="space-y-4">
                  <ChartContainer config={chartConfig} className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Line 
                          type="monotone" 
                          dataKey="fires" 
                          stroke="var(--color-fires)" 
                          strokeWidth={2}
                          dot={{ fill: "var(--color-fires)" }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="threats" 
                          stroke="var(--color-threats)" 
                          strokeWidth={2}
                          dot={{ fill: "var(--color-threats)" }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </TabsContent>

                <TabsContent value="severity" className="space-y-4">
                  <ChartContainer config={chartConfig} className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={severityData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={120}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {severityData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <ChartTooltip content={<ChartTooltipContent />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </TabsContent>

                <TabsContent value="temperature" className="space-y-4">
                  <ChartContainer config={chartConfig} className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Area 
                          type="monotone" 
                          dataKey="temperature" 
                          stroke="var(--color-temperature)" 
                          fill="var(--color-temperature)"
                          fillOpacity={0.3}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Fire List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Flame className="h-5 w-5" />
                Active Incidents
              </CardTitle>
              <CardDescription>
                Current wildfire incidents with real-time status updates
              </CardDescription>
              
              {/* Filters */}
              <div className="flex flex-col sm:flex-row gap-3 pt-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search fires by name or location..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={severityFilter} onValueChange={setSeverityFilter}>
                  <SelectTrigger className="w-full sm:w-[180px]">
                    <SelectValue placeholder="Filter by severity" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Severities</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="moderate">Moderate</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="extreme">Extreme</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fire Name</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Size (acres)</TableHead>
                    <TableHead>Containment</TableHead>
                    <TableHead>Threat Level</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredFires.map((fire) => (
                    <TableRow key={fire.id} className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
                      <TableCell className="font-medium">{fire.name}</TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">{fire.location}</TableCell>
                      <TableCell>
                        <SeverityBadge severity={fire.severity} />
                      </TableCell>
                      <TableCell>{fire.size.toLocaleString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={fire.containment} className="w-16" />
                          <span className="text-sm">{fire.containment}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <div className={`w-2 h-2 rounded-full ${
                            fire.threatLevel >= 8 ? 'bg-red-500' :
                            fire.threatLevel >= 6 ? 'bg-orange-500' :
                            fire.threatLevel >= 4 ? 'bg-yellow-500' : 'bg-green-500'
                          }`} />
                          {fire.threatLevel}/10
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedFire(fire)}
                          className="flex items-center gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - 3D Globe and Details */}
        <div className="space-y-6">
          {/* 3D Globe */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Global Fire Map
              </CardTitle>
              <CardDescription>
                Interactive 3D visualization of active wildfire locations
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <Globe3D className="w-full max-w-[300px]" />
            </CardContent>
          </Card>

          {/* Weather Conditions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wind className="h-5 w-5" />
                Weather Conditions
              </CardTitle>
              <CardDescription>
                Current environmental factors affecting fire behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Thermometer className="h-4 w-4 text-red-500" />
                    <span className="text-sm font-medium">Temperature</span>
                  </div>
                  <div className="text-2xl font-bold text-red-600">95°F</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Droplets className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">Humidity</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">15%</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Wind className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-medium">Wind Speed</span>
                  </div>
                  <div className="text-2xl font-bold text-green-600">35 mph</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Eye className="h-4 w-4 text-purple-500" />
                    <span className="text-sm font-medium">Visibility</span>
                  </div>
                  <div className="text-2xl font-bold text-purple-600">2.5 mi</div>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-3">
                <h4 className="font-medium">Risk Factors</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Wind Conditions</span>
                    <Badge variant="destructive">High Risk</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Humidity Levels</span>
                    <Badge variant="destructive">Critical</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Temperature</span>
                    <Badge className="bg-orange-100 text-orange-800">Elevated</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Satellite Data */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Satellite className="h-5 w-5" />
                Satellite Data
              </CardTitle>
              <CardDescription>
                Latest NASA satellite imagery and detection data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Last Satellite Pass</span>
                  <span className="text-sm font-medium">14:25 UTC</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Data Quality</span>
                  <Badge className="bg-green-100 text-green-800">Excellent</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Cloud Coverage</span>
                  <span className="text-sm font-medium">12%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Resolution</span>
                  <span className="text-sm font-medium">375m</span>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <h4 className="font-medium">Detection Confidence</h4>
                <Progress value={92} className="w-full" />
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  92% confidence in fire detection algorithms
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Fire Detail Modal */}
      <AnimatePresence>
        {selectedFire && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedFire(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-slate-900 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                      {selectedFire.name}
                    </h2>
                    <p className="text-slate-600 dark:text-slate-400 flex items-center gap-1 mt-1">
                      <MapPin className="h-4 w-4" />
                      {selectedFire.location}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedFire(null)}
                  >
                    Close
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold mb-3">Fire Details</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span>Severity:</span>
                          <SeverityBadge severity={selectedFire.severity} />
                        </div>
                        <div className="flex justify-between">
                          <span>Size:</span>
                          <span className="font-medium">{selectedFire.size.toLocaleString()} acres</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Containment:</span>
                          <span className="font-medium">{selectedFire.containment}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Threat Level:</span>
                          <span className="font-medium">{selectedFire.threatLevel}/10</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-3">Weather Conditions</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span>Temperature:</span>
                          <span className="font-medium">{selectedFire.temperature}°F</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Humidity:</span>
                          <span className="font-medium">{selectedFire.humidity}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Wind Speed:</span>
                          <span className="font-medium">{selectedFire.windSpeed} mph</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Wind Direction:</span>
                          <span className="font-medium">{selectedFire.windDirection}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold mb-3">Response Resources</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span>Personnel:</span>
                          <span className="font-medium">{selectedFire.resources.personnel}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Aircraft:</span>
                          <span className="font-medium">{selectedFire.resources.aircraft}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Ground Vehicles:</span>
                          <span className="font-medium">{selectedFire.resources.groundVehicles}</span>
                        </div>
                      </div>
                    </div>

                    {selectedFire.evacuationZones.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-3">Evacuation Zones</h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedFire.evacuationZones.map((zone) => (
                            <Badge key={zone} variant="destructive">
                              {zone}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <h3 className="font-semibold mb-3">Last Updated</h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {new Date(selectedFire.lastUpdated).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button className="flex-1">
                    <Zap className="h-4 w-4 mr-2" />
                    Emergency Response
                  </Button>
                  <Button variant="outline" className="flex-1">
                    <Download className="h-4 w-4 mr-2" />
                    Download Report
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function WildfireDashboard() {
  return <WildfireMonitoringDashboard />
}
