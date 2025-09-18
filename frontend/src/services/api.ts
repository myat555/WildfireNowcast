// API service for integrating with WildfireNowcast backend

export interface WildfireData {
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

export interface NASAFIRMSData {
  timestamp: string
  area: string
  days_back: number
  satellite: string
  confidence: string
  format: string
  hotspot_count: number
  hotspots: Array<{
    latitude: number
    longitude: number
    brightness: number
    scan: number
    track: number
    acq_date: string
    acq_time: string
    satellite: string
    confidence: string
    version: string
    bright_t31: number
    frp: number
    daynight: string
  }>
  data_source: string
  api_version: string
}

export interface GIBSData {
  timestamp: string
  layer_name: string
  bbox: string
  size: string
  date: string
  projection: string
  format: string
  image_data: string
  image_size_bytes: number
  data_source: string
}

export interface EONETData {
  timestamp: string
  category: string
  days_back: number
  status: string
  limit: number
  source: string | null
  event_count: number
  events: Array<{
    id: string
    title: string
    description: string
    link: string
    categories: string[]
    sources: string[]
    geometry: any
    date: string
    status: string
    closed: string | null
  }>
  data_source: string
}

class WildfireAPI {
  private baseURL: string

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || '/api'
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      throw error
    }
  }

  // NASA FIRMS API endpoints
  async getFIRMSHotspots(
    area: string = "global",
    daysBack: number = 1,
    confidence: string = "nominal",
    satellite: string = "both"
  ): Promise<NASAFIRMSData> {
    return this.request<NASAFIRMSData>(
      `/firms-hotspots?area=${area}&days_back=${daysBack}&confidence=${confidence}&satellite=${satellite}`
    )
  }

  // GIBS API endpoints
  async getGIBSMapImage(
    layerName: string = "MODIS_Terra_CorrectedReflectance_TrueColor",
    bbox: string = "-180,-90,180,90",
    size: string = "1200,600",
    date?: string,
    projection: string = "epsg4326"
  ): Promise<GIBSData> {
    const params = new URLSearchParams({
      layer_name: layerName,
      bbox,
      size,
      projection,
    })
    
    if (date) {
      params.append('date', date)
    }

    return this.request<GIBSData>(`/gibs-map-image?${params.toString()}`)
  }

  // EONET API endpoints
  async getEONETEvents(
    category: string = "wildfires",
    daysBack: number = 30,
    status: string = "open",
    limit: number = 100,
    source?: string
  ): Promise<EONETData> {
    const params = new URLSearchParams({
      category,
      days_back: daysBack.toString(),
      status,
      limit: limit.toString(),
    })
    
    if (source) {
      params.append('source', source)
    }

    return this.request<EONETData>(`/eonet-events?${params.toString()}`)
  }

  // Threat assessment endpoints
  async getThreatAssessment(hotspotsData: any, assetsData?: any): Promise<any> {
    return this.request('/threat-assessment', {
      method: 'POST',
      body: JSON.stringify({
        hotspots_data: hotspotsData,
        assets_data: assetsData,
      }),
    })
  }

  // Mapping endpoints
  async generateFireMap(
    hotspotsData: any,
    assetsData?: any,
    mapCenter?: [number, number],
    zoomLevel?: number
  ): Promise<any> {
    return this.request('/fire-map', {
      method: 'POST',
      body: JSON.stringify({
        hotspots_data: hotspotsData,
        assets_data: assetsData,
        map_center: mapCenter,
        zoom_level: zoomLevel,
      }),
    })
  }

  // ICS reporting endpoints
  async generateICSReport(
    hotspotsData: any,
    threatData?: any,
    evacuationData?: any,
    incidentName?: string,
    incidentNumber?: string
  ): Promise<any> {
    return this.request('/ics-report', {
      method: 'POST',
      body: JSON.stringify({
        hotspots_data: hotspotsData,
        threat_data: threatData,
        evacuation_data: evacuationData,
        incident_name: incidentName,
        incident_number: incidentNumber,
      }),
    })
  }

  // Agent query endpoint
  async queryAgent(prompt: string): Promise<string> {
    return this.request('/agent-query', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health')
  }
}

// Create singleton instance
export const wildfireAPI = new WildfireAPI()

// Utility functions for data transformation
export const transformFIRMSToWildfireData = (firmsData: NASAFIRMSData): WildfireData[] => {
  return firmsData.hotspots.map((hotspot, index) => ({
    id: `WF${String(index + 1).padStart(3, '0')}`,
    name: `Fire ${index + 1}`,
    location: `${hotspot.latitude.toFixed(4)}, ${hotspot.longitude.toFixed(4)}`,
    coordinates: [hotspot.latitude, hotspot.longitude],
    severity: hotspot.confidence === 'high' ? 'extreme' : 
              hotspot.confidence === 'nominal' ? 'high' : 
              hotspot.confidence === 'low' ? 'moderate' : 'low',
    size: Math.random() * 10000 + 1000, // Mock size calculation
    containment: Math.random() * 100, // Mock containment
    lastUpdated: new Date().toISOString(),
    temperature: Math.random() * 30 + 70, // Mock temperature
    humidity: Math.random() * 50 + 10, // Mock humidity
    windSpeed: Math.random() * 40 + 5, // Mock wind speed
    windDirection: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.floor(Math.random() * 8)],
    threatLevel: Math.random() * 10,
    evacuationZones: [],
    resources: {
      personnel: Math.floor(Math.random() * 500 + 50),
      aircraft: Math.floor(Math.random() * 20 + 2),
      groundVehicles: Math.floor(Math.random() * 100 + 10),
    }
  }))
}

export default wildfireAPI
