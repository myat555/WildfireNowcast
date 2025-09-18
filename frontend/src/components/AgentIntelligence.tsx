"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Brain, 
  Zap, 
  Eye, 
  TrendingUp, 
  AlertTriangle,
  Shield,
  MapPin,
  Clock,
  CheckCircle,
  ArrowRight,
  Sparkles,
  Activity,
  Target,
  Lightbulb
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

interface AgentThought {
  id: string
  step: string
  description: string
  status: "thinking" | "analyzing" | "completed"
  duration: number
  insights: string[]
}

interface AgentAnalysis {
  threatLevel: number
  confidence: number
  recommendations: string[]
  dataPoints: number
  toolsUsed: string[]
  processingTime: number
}

export function AgentIntelligence() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [currentThought, setCurrentThought] = useState<AgentThought | null>(null)
  const [analysis, setAnalysis] = useState<AgentAnalysis | null>(null)
  const [thoughts, setThoughts] = useState<AgentThought[]>([])

  const simulateAgentThinking = async () => {
    setIsAnalyzing(true)
    setThoughts([])
    setAnalysis(null)

    const thinkingSteps: Omit<AgentThought, 'id'>[] = [
      {
        step: "Data Ingestion",
        description: "Retrieving NASA FIRMS satellite data for California region",
        status: "thinking",
        duration: 1500,
        insights: ["8 active hotspots detected", "MODIS/VIIRS data processed", "3-hour data freshness confirmed"]
      },
      {
        step: "Threat Assessment",
        description: "Analyzing proximity to critical infrastructure and populated areas",
        status: "thinking",
        duration: 2000,
        insights: ["3 power substations at risk", "2 water treatment facilities threatened", "15,000 residents in danger zone"]
      },
      {
        step: "Weather Analysis",
        description: "Processing meteorological data for fire behavior prediction",
        status: "thinking",
        duration: 1800,
        insights: ["Northeast winds at 35 mph", "Humidity below 20%", "Temperature rising to 95°F"]
      },
      {
        step: "Resource Planning",
        description: "Calculating optimal resource allocation and deployment",
        status: "thinking",
        duration: 2200,
        insights: ["Need 15 additional aircraft", "200 more personnel required", "Ground vehicles insufficient"]
      },
      {
        step: "Evacuation Planning",
        description: "Determining evacuation zones and optimal routes",
        status: "thinking",
        duration: 1600,
        insights: ["Zone A: Immediate evacuation", "Zone B: Prepare for evacuation", "3 evacuation routes identified"]
      },
      {
        step: "Report Generation",
        description: "Compiling comprehensive ICS situation report",
        status: "thinking",
        duration: 1200,
        insights: ["SITREP generated", "Resource requests prepared", "Command briefing ready"]
      }
    ]

    for (let i = 0; i < thinkingSteps.length; i++) {
      const step = thinkingSteps[i]
      const thought: AgentThought = {
        id: `thought-${i}`,
        ...step
      }

      setCurrentThought(thought)
      setThoughts(prev => [...prev, thought])

      // Simulate thinking time
      await new Promise(resolve => setTimeout(resolve, step.duration))

      // Mark as completed
      setThoughts(prev => prev.map(t => 
        t.id === thought.id ? { ...t, status: "completed" } : t
      ))
    }

    // Generate final analysis
    const finalAnalysis: AgentAnalysis = {
      threatLevel: 9.2,
      confidence: 94,
      recommendations: [
        "Immediate evacuation of Zone A (2,500 residents)",
        "Deploy additional aircraft for aerial suppression",
        "Establish incident command post at coordinates 34.0522, -118.2437",
        "Request mutual aid from neighboring counties",
        "Activate emergency alert system for affected zones"
      ],
      dataPoints: 1247,
      toolsUsed: [
        "fetch_firms_hotspots_enhanced",
        "assess_asset_threats", 
        "generate_threat_summary",
        "calculate_evacuation_zones",
        "draft_ics_situation_report"
      ],
      processingTime: 10.3
    }

    setAnalysis(finalAnalysis)
    setIsAnalyzing(false)
    setCurrentThought(null)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "thinking": return "text-blue-500"
      case "analyzing": return "text-yellow-500"
      case "completed": return "text-green-500"
      default: return "text-gray-500"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "thinking": return <Brain className="h-4 w-4 animate-pulse" />
      case "analyzing": return <Activity className="h-4 w-4 animate-spin" />
      case "completed": return <CheckCircle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Agent Intelligence Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-blue-600" />
            Agent Intelligence in Action
          </CardTitle>
          <CardDescription>
            Watch the WildfireNowcast Agent analyze wildfire data and generate insights
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                The agent is continuously monitoring NASA satellite data and analyzing threats in real-time.
              </p>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span>Active Monitoring</span>
                </div>
                <div className="flex items-center gap-1">
                  <Sparkles className="h-4 w-4 text-yellow-500" />
                  <span>AI-Powered Analysis</span>
                </div>
                <div className="flex items-center gap-1">
                  <Target className="h-4 w-4 text-blue-500" />
                  <span>Real-time Insights</span>
                </div>
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={simulateAgentThinking}
              disabled={isAnalyzing}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <Activity className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Start Analysis
                </>
              )}
            </motion.button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Thinking Process */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Agent Thinking Process
            </CardTitle>
            <CardDescription>
              Step-by-step analysis of the agent's decision-making process
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {thoughts.map((thought, index) => (
                <motion.div
                  key={thought.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`p-4 rounded-lg border ${
                    thought.status === "completed" 
                      ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20"
                      : thought.status === "thinking"
                      ? "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20"
                      : "border-slate-200 dark:border-slate-700"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${
                      thought.status === "completed" 
                        ? "bg-green-100 dark:bg-green-900/40"
                        : thought.status === "thinking"
                        ? "bg-blue-100 dark:bg-blue-900/40"
                        : "bg-slate-100 dark:bg-slate-800"
                    }`}>
                      {getStatusIcon(thought.status)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm">{thought.step}</h4>
                        <Badge variant={
                          thought.status === "completed" ? "default" :
                          thought.status === "thinking" ? "secondary" : "outline"
                        }>
                          {thought.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                        {thought.description}
                      </p>
                      {thought.insights.length > 0 && (
                        <div className="space-y-1">
                          {thought.insights.map((insight, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs">
                              <ArrowRight className="h-3 w-3 text-green-500" />
                              <span className="text-slate-600 dark:text-slate-400">{insight}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}

              {currentThought && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-4 rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/40">
                      <Activity className="h-4 w-4 animate-spin text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm">{currentThought.step}</h4>
                        <Badge variant="secondary">Processing</Badge>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {currentThought.description}
                      </p>
                      <div className="mt-2">
                        <Progress value={75} className="h-1" />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Analysis Results
            </CardTitle>
            <CardDescription>
              Comprehensive threat assessment and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {analysis ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Threat Level */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Threat Level</span>
                    <Badge variant="destructive" className="text-lg px-3 py-1">
                      {analysis.threatLevel}/10
                    </Badge>
                  </div>
                  <Progress value={analysis.threatLevel * 10} className="h-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Critical threat level requiring immediate action
                  </p>
                </div>

                {/* Confidence */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Analysis Confidence</span>
                    <span className="text-lg font-bold text-green-600">{analysis.confidence}%</span>
                  </div>
                  <Progress value={analysis.confidence} className="h-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    High confidence based on {analysis.dataPoints.toLocaleString()} data points
                  </p>
                </div>

                {/* Processing Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{analysis.dataPoints}</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Data Points</div>
                  </div>
                  <div className="text-center p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{analysis.processingTime}s</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Processing Time</div>
                  </div>
                </div>

                {/* Tools Used */}
                <div className="space-y-2">
                  <h4 className="font-medium">AI Tools Used</h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.toolsUsed.map((tool) => (
                      <Badge key={tool} variant="outline" className="text-xs">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    AI Recommendations
                  </h4>
                  <div className="space-y-2">
                    {analysis.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0" />
                        <span className="text-sm">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Click "Start Analysis" to see the agent's intelligence in action</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Agent Capabilities Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Agent Capabilities Overview
          </CardTitle>
          <CardDescription>
            The WildfireNowcast Agent's comprehensive toolkit for emergency response
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <h4 className="font-medium">Fire Detection</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                Real-time NASA satellite fire detection with 98.7% accuracy
              </p>
              <Badge variant="outline" className="text-xs">MODIS/VIIRS</Badge>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="h-5 w-5 text-blue-500" />
                <h4 className="font-medium">Threat Assessment</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                AI-powered analysis of threats to critical infrastructure
              </p>
              <Badge variant="outline" className="text-xs">Machine Learning</Badge>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="h-5 w-5 text-green-500" />
                <h4 className="font-medium">Live Mapping</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                Dynamic fire progression mapping and visualization
              </p>
              <Badge variant="outline" className="text-xs">GIS Analysis</Badge>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-5 w-5 text-purple-500" />
                <h4 className="font-medium">ICS Reporting</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                Automated Incident Command System report generation
              </p>
              <Badge variant="outline" className="text-xs">Emergency Management</Badge>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                <h4 className="font-medium">Resource Planning</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                Intelligent resource allocation and deployment recommendations
              </p>
              <Badge variant="outline" className="text-xs">Optimization</Badge>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Eye className="h-5 w-5 text-orange-500" />
                <h4 className="font-medium">Evacuation Planning</h4>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                AI-driven evacuation zone calculation and route planning
              </p>
              <Badge variant="outline" className="text-xs">Safety Analysis</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AgentIntelligence
