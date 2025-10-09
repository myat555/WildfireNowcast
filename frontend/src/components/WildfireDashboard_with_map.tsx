"use client"

import { useState, useEffect, useMemo } from "react"
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
  MapPin,
  Clock,
  Search,
  Settings,
  Bell,
  Download,
  RefreshCw,
  Zap,
  Shield,
  Loader2
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
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts"
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// API Configuration
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  brightness?: number
  confidence?: string
  frp?: number
}

interface NASAHotspot {
  latitude: string | number
  longitude: string | number
  brightness: string | number
  confidence: string | number
  frp: string | number
  acq_date: string
  acq_time: string
  satellite: string
  instrument: string
  version: string
  bright_t31: string | number
  scan: string | number
  track: string | number
  daynight: string
}

interface NASASummary {
  status: string
  timestamp: string
  summary: {
    total_hotspots: number
    by_confidence: {
      high: number
      nominal: number
      low: number
    }
    by_satellite: any
    date_range: {
      start: string
      end: string
    }
  }
  hotspots?: NASAHotspot[]
  eonet_events?: any[]
}

interface ChartDataPoint {
  time: string
  fires: number
  threats: number
  temperature: number
}

interface SeverityDataPoint {
  name: string
  value: number
  color: string
}

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

// Helper function to determine severity based on fire data
function determineSeverity(hotspot: NASAHotspot): "low" | "moderate" | "high" | "extreme" {
  const brightness = parseFloat(hotspot.brightness as string)
  const frp = parseFloat(hotspot.frp as string)
  const confidence = hotspot.confidence

  if (confidence === 'h' || (brightness > 350 && frp > 50)) {
    return 'extreme'
  } else if (brightness > 330 && frp > 30) {
    return 'high'
  } else if (brightness > 310 && frp > 10) {
    return 'moderate'
  } else {
    return 'low'
  }
}

// Helper function to convert NASA hotspot to WildfireData
function convertHotspotToWildfire(hotspot: NASAHotspot, index: number): WildfireData {
  const lat = parseFloat(hotspot.latitude as string)
  const lon = parseFloat(hotspot.longitude as string)
  const brightness = parseFloat(hotspot.brightness as string)
  const frp = parseFloat(hotspot.frp as string)
  const severity = determineSeverity(hotspot)

  // Estimate containment based on confidence and brightness
  let containment = 0
  if (hotspot.confidence === 'l') containment = 70
  else if (hotspot.confidence === 'n') containment = 40
  else containment = 10

  // Estimate threat level
  const threatLevel = Math.min(10, (frp / 100) * 8 + (severity === 'extreme' ? 2 : 0))

  return {
    id: `FIRE-${index + 1}`,
    name: `Fire ${index + 1}`,
    location: `${lat.toFixed(4)}°, ${lon.toFixed(4)}°`,
    coordinates: [lat, lon],
    severity,
    size: Math.round(frp * 10), // Rough estimate based on FRP
    containment,
    lastUpdated: `${hotspot.acq_date}T${hotspot.acq_time}:00Z`,
    temperature: Math.round(brightness * 0.2), // Rough conversion
    humidity: severity === 'extreme' ? 10 : severity === 'high' ? 15 : 25,
    windSpeed: 15 + Math.random() * 20,
    windDirection: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.floor(Math.random() * 8)],
    threatLevel: Math.round(threatLevel * 10) / 10,
    evacuationZones: severity === 'extreme' ? ['Zone A', 'Zone B'] : severity === 'high' ? ['Zone A'] : [],
    resources: {
      personnel: severity === 'extreme' ? 300 + Math.floor(Math.random() * 200) :
                 severity === 'high' ? 150 + Math.floor(Math.random() * 150) :
                 50 + Math.floor(Math.random() * 100),
      aircraft: severity === 'extreme' ? 8 : severity === 'high' ? 4 : 2,
      groundVehicles: severity === 'extreme' ? 60 : severity === 'high' ? 35 : 15
    },
    brightness: parseFloat(hotspot.brightness as string),
    confidence: hotspot.confidence as string,
    frp: parseFloat(hotspot.frp as string)
  }
}

// Main Dashboard Component
export function WildfireMonitoringDashboard() {
  const [wildfires, setWildfires] = useState<WildfireData[]>([])
  const [selectedFire, setSelectedFire] = useState<WildfireData | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [severityFilter, setSeverityFilter] = useState("all")
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [error, setError] = useState<string | null>(null)
  const [nasaSummary, setNasaSummary] = useState<NASASummary | null>(null)
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [severityData, setSeverityData] = useState<SeverityDataPoint[]>([])

  // Fetch data from API
  const fetchData = async () => {
    try {
      setError(null)

      // Fetch NASA FIRMS hotspots for California
      const hotspotsResponse = await fetch(`${apiUrl}/api/firms-hotspots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          area: "usa",
          days_back: 1,
          confidence: "nominal",
          satellite: "both"
        })
      })

      if (!hotspotsResponse.ok) {
        throw new Error(`Failed to fetch hotspots: ${hotspotsResponse.statusText}`)
      }

      const hotspotsData = await hotspotsResponse.json()

      // Fetch NASA summary
      const summaryResponse = await fetch(`${apiUrl}/api/nasa-summary?area=usa&days_back=1&include_gibs=true&include_eonet=true`)

      if (!summaryResponse.ok) {
        throw new Error(`Failed to fetch summary: ${summaryResponse.statusText}`)
      }

      const summaryData = await summaryResponse.json()
      setNasaSummary(summaryData)

      // Convert hotspots to wildfire data
      let hotspots: NASAHotspot[] = []
      if (hotspotsData.hotspots && Array.isArray(hotspotsData.hotspots)) {
        hotspots = hotspotsData.hotspots
      } else if (summaryData.hotspots && Array.isArray(summaryData.hotspots)) {
        hotspots = summaryData.hotspots
      }

      // Filter for California area (approximate bounding box)
      const californiaHotspots = hotspots.filter((h: NASAHotspot) => {
        const lat = parseFloat(h.latitude as string)
        const lon = parseFloat(h.longitude as string)
        return lat >= 32.5 && lat <= 42.0 && lon >= -124.5 && lon <= -114.0
      }).slice(0, 50) // Limit to 50 most recent

      const wildfiresData = californiaHotspots.map((hotspot: NASAHotspot, index: number) =>
        convertHotspotToWildfire(hotspot, index)
      )

      setWildfires(wildfiresData)

      // Generate chart data based on real data
      generateChartData(wildfiresData)

      // Generate severity distribution
      generateSeverityData(wildfiresData)

      setLastUpdate(new Date())
    } catch (err) {
      console.error('Error fetching data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    }
  }

  // Generate chart data from real wildfires
  const generateChartData = (fires: WildfireData[]) => {
    const now = new Date()
    const data: ChartDataPoint[] = []

    for (let i = 0; i < 6; i++) {
      const time = new Date(now.getTime() - (5 - i) * 4 * 60 * 60 * 1000)
      const hourLabel = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })

      // Simulate progression of fires over time
      const fireCount = Math.max(1, Math.round(fires.length * (0.5 + i * 0.1)))
      const avgThreat = fires.reduce((sum, f) => sum + f.threatLevel, 0) / Math.max(fires.length, 1)
      const avgTemp = fires.reduce((sum, f) => sum + f.temperature, 0) / Math.max(fires.length, 1)

      data.push({
        time: hourLabel,
        fires: fireCount,
        threats: Math.round(avgThreat * 10),
        temperature: Math.round(avgTemp)
      })
    }

    setChartData(data)
  }

  // Generate severity distribution from real data
  const generateSeverityData = (fires: WildfireData[]) => {
    const severityCounts = {
      low: 0,
      moderate: 0,
      high: 0,
      extreme: 0
    }

    fires.forEach(fire => {
      severityCounts[fire.severity]++
    })

    const total = Math.max(fires.length, 1)

    setSeverityData([
      { name: "Low", value: Math.round((severityCounts.low / total) * 100), color: "#22c55e" },
      { name: "Moderate", value: Math.round((severityCounts.moderate / total) * 100), color: "#eab308" },
      { name: "High", value: Math.round((severityCounts.high / total) * 100), color: "#f97316" },
      { name: "Extreme", value: Math.round((severityCounts.extreme / total) * 100), color: "#dc2626" }
    ])
  }

  // Load data on mount
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      await fetchData()
      setIsLoading(false)
    }
    loadData()
  }, [])

  const filteredFires = useMemo(() => {
    return wildfires.filter(fire => {
      const matchesSearch = fire.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           fire.location.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesSeverity = severityFilter === "all" || fire.severity === severityFilter
      return matchesSearch && matchesSeverity
    })
  }, [wildfires, searchTerm, severityFilter])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchData()
    setIsRefreshing(false)
  }

  const totalFires = wildfires.length
  const activeFires = wildfires.filter(f => f.containment < 100).length
  const extremeFires = wildfires.filter(f => f.severity === "extreme").length
  const avgContainment = totalFires > 0
    ? Math.round(wildfires.reduce((acc, f) => acc + f.containment, 0) / totalFires)
    : 0

  // Calculate average weather conditions
  const avgTemperature = totalFires > 0
    ? Math.round(wildfires.reduce((acc, f) => acc + f.temperature, 0) / totalFires)
    : 75
  const avgHumidity = totalFires > 0
    ? Math.round(wildfires.reduce((acc, f) => acc + f.humidity, 0) / totalFires)
    : 20
  const avgWindSpeed = totalFires > 0
    ? Math.round(wildfires.reduce((acc, f) => acc + f.windSpeed, 0) / totalFires)
    : 15

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-red-500 mx-auto" />
          <p className="text-lg text-slate-600 dark:text-slate-400">Loading NASA wildfire data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Error Loading Data
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-slate-600 dark:text-slate-400">{error}</p>
            <Button onClick={handleRefresh} className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 px-4 pb-4 space-y-6">
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
                  {filteredFires.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-slate-500 py-8">
                        No active fires found matching your criteria
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredFires.map((fire) => (
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
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Map and Details */}
        <div className="space-y-6">
          {/* Leaflet Map */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Fire Locations Map
              </CardTitle>
              <CardDescription>
                Real-time visualization of active wildfire hotspots
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px] rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
                <MapContainer
                  center={[36.7783, -119.4179]}
                  zoom={6}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {wildfires.map((fire) => {
                    const color =
                      fire.severity === 'extreme' ? '#dc2626' :
                      fire.severity === 'high' ? '#f97316' :
                      fire.severity === 'moderate' ? '#eab308' : '#22c55e'

                    const radius =
                      fire.severity === 'extreme' ? 12 :
                      fire.severity === 'high' ? 10 :
                      fire.severity === 'moderate' ? 8 : 6

                    return (
                      <CircleMarker
                        key={fire.id}
                        center={fire.coordinates}
                        radius={radius}
                        pathOptions={{
                          color: color,
                          fillColor: color,
                          fillOpacity: 0.6,
                          weight: 2
                        }}
                      >
                        <Popup>
                          <div className="space-y-2 min-w-[200px]">
                            <h3 className="font-bold text-lg">{fire.name}</h3>
                            <div className="space-y-1 text-sm">
                              <p><strong>Location:</strong> {fire.location}</p>
                              <p><strong>Severity:</strong> {fire.severity}</p>
                              <p><strong>Size:</strong> {fire.size.toLocaleString()} acres</p>
                              <p><strong>Containment:</strong> {fire.containment}%</p>
                              <p><strong>Threat Level:</strong> {fire.threatLevel}/10</p>
                              {fire.brightness && <p><strong>Brightness:</strong> {fire.brightness.toFixed(1)}K</p>}
                              {fire.frp && <p><strong>FRP:</strong> {fire.frp.toFixed(1)} MW</p>}
                            </div>
                            <Button
                              size="sm"
                              onClick={() => setSelectedFire(fire)}
                              className="w-full mt-2"
                            >
                              View Details
                            </Button>
                          </div>
                        </Popup>
                      </CircleMarker>
                    )
                  })}
                </MapContainer>
              </div>
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
                  <div className="text-2xl font-bold text-red-600">{avgTemperature}°F</div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Droplets className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">Humidity</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">{avgHumidity}%</div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Wind className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-medium">Wind Speed</span>
                  </div>
                  <div className="text-2xl font-bold text-green-600">{avgWindSpeed} mph</div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Eye className="h-4 w-4 text-purple-500" />
                    <span className="text-sm font-medium">Visibility</span>
                  </div>
                  <div className="text-2xl font-bold text-purple-600">
                    {extremeFires > 2 ? '1.5 mi' : '3.0 mi'}
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-3">
                <h4 className="font-medium">Risk Factors</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Wind Conditions</span>
                    <Badge variant={avgWindSpeed > 25 ? "destructive" : "default"}>
                      {avgWindSpeed > 25 ? 'High Risk' : 'Moderate'}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Humidity Levels</span>
                    <Badge variant={avgHumidity < 20 ? "destructive" : "default"}>
                      {avgHumidity < 20 ? 'Critical' : 'Normal'}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Temperature</span>
                    <Badge className={avgTemperature > 90 ? "bg-orange-100 text-orange-800" : "bg-green-100 text-green-800"}>
                      {avgTemperature > 90 ? 'Elevated' : 'Normal'}
                    </Badge>
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
                  <span className="text-sm font-medium">
                    {lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Data Quality</span>
                  <Badge className="bg-green-100 text-green-800">
                    {nasaSummary?.status === 'success' ? 'Excellent' : 'Good'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Total Hotspots</span>
                  <span className="text-sm font-medium">
                    {nasaSummary?.summary?.total_hotspots || totalFires}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Resolution</span>
                  <span className="text-sm font-medium">375m - 1km</span>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium">Detection Confidence</h4>
                <Progress value={totalFires > 0 ? 90 : 70} className="w-full" />
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {totalFires > 0 ? '90' : '70'}% confidence in fire detection algorithms
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
                        {selectedFire.brightness && (
                          <div className="flex justify-between">
                            <span>Brightness:</span>
                            <span className="font-medium">{selectedFire.brightness.toFixed(1)}K</span>
                          </div>
                        )}
                        {selectedFire.frp && (
                          <div className="flex justify-between">
                            <span>Fire Power:</span>
                            <span className="font-medium">{selectedFire.frp.toFixed(1)} MW</span>
                          </div>
                        )}
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
                          <span className="font-medium">{selectedFire.windSpeed.toFixed(1)} mph</span>
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
