"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Bot,
  MessageSquare,
  Send,
  Loader2,
  Copy,
  RefreshCw
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

// Types for agent interactions
interface AgentMessage {
  id: string
  type: "user" | "agent"
  content: string
  timestamp: Date
  status?: "thinking" | "success" | "error"
  toolsUsed?: string[]
  dataInsights?: string[]
  recommendations?: string[]
}

// Example queries that showcase agent capabilities
const exampleQueries = [
  "Check for wildfire hotspots in California",
  "Assess threats to critical infrastructure near current fires",
  "Generate a live map of current fire activity",
  "Draft an ICS situation report for current fires",
  "Recommend resource deployment for active incidents",
  "Calculate evacuation zones for active fires",
  "What's the fire progression over the last 24 hours?",
  "Which fires pose the highest risk to populated areas?"
]

export function AgentShowcase() {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [agentStatus, setAgentStatus] = useState<"idle" | "thinking" | "active">("idle")

  // Process agent query with real API
  const processQuery = async (query: string) => {
    setIsProcessing(true)
    setAgentStatus("thinking")

    // Add user message
    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      type: "user",
      content: query,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])

    try {
      // Call real backend API
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/agent-query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: query,
          enable_trace: false
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()

      const agentMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        type: "agent",
        content: data.response || data.message || "No response from agent",
        timestamp: new Date(),
        status: "success",
        toolsUsed: data.tools_used || [],
        dataInsights: data.data_insights || [],
        recommendations: data.recommendations || []
      }

      setMessages(prev => [...prev, agentMessage])
      setAgentStatus("active")
    } catch (error) {
      console.error("Agent query error:", error)

      // Fallback to mock response on error
      const agentResponse = generateAgentResponse(query)

      const agentMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        type: "agent",
        content: `⚠️ Using demo mode. ${agentResponse.content}`,
        timestamp: new Date(),
        status: "success",
        toolsUsed: agentResponse.toolsUsed,
        dataInsights: agentResponse.dataInsights,
        recommendations: agentResponse.recommendations
      }

      setMessages(prev => [...prev, agentMessage])
      setAgentStatus("idle")
    } finally {
      setIsProcessing(false)
    }
  }

  const generateAgentResponse = (query: string) => {
    const lowerQuery = query.toLowerCase()

    if (lowerQuery.includes("hotspot") || lowerQuery.includes("fire")) {
      return {
        content: "I've analyzed NASA FIRMS satellite data and detected 8 active wildfire hotspots in California. The Canyon Fire in Los Angeles County shows extreme severity with 15,420 acres burned and only 25% containment. I've identified critical threats to infrastructure and populated areas.",
        toolsUsed: ["fetch_firms_hotspots_enhanced", "assess_asset_threats", "generate_threat_summary"],
        dataInsights: [
          "8 active fires detected via MODIS/VIIRS satellites",
          "Canyon Fire poses immediate threat to 3 power substations",
          "Fire progression rate: 2.3 acres/minute",
          "Wind conditions accelerating spread toward populated areas"
        ],
        recommendations: [
          "Immediate evacuation of Zone A (2,500 residents)",
          "Deploy additional aircraft for aerial suppression",
          "Establish incident command post at coordinates 34.0522, -118.2437",
          "Request mutual aid from neighboring counties"
        ]
      }
    } else if (lowerQuery.includes("map") || lowerQuery.includes("visualization")) {
      return {
        content: "I've generated a comprehensive live fire map showing current fire perimeters, evacuation zones, and threat assessments. The map integrates NASA satellite imagery with real-time fire progression data and critical infrastructure locations.",
        toolsUsed: ["fetch_gibs_map_image", "generate_fire_map", "create_progression_map"],
        dataInsights: [
          "Fire perimeter expanded 40% in last 2 hours",
          "Evacuation zones cover 15,000 residents",
          "Critical infrastructure within 2-mile radius of fire",
          "Optimal evacuation routes identified and mapped"
        ],
        recommendations: [
          "Activate emergency alert system for affected zones",
          "Deploy traffic control for evacuation routes",
          "Establish temporary shelters at safe locations",
          "Coordinate with local emergency services"
        ]
      }
    } else if (lowerQuery.includes("report") || lowerQuery.includes("ics")) {
      return {
        content: "I've drafted a comprehensive ICS Situation Report (SITREP) for the Canyon Fire incident. The report includes current fire status, resource deployment, threat assessment, and recommended actions for command staff.",
        toolsUsed: ["draft_ics_situation_report", "create_resource_recommendations", "generate_incident_briefing"],
        dataInsights: [
          "Incident classified as Type 1 (most complex)",
          "Current resource commitment: $2.3M",
          "Projected containment: 48-72 hours",
          "Risk to life and property: HIGH"
        ],
        recommendations: [
          "Request Type 1 Incident Management Team",
          "Implement unified command structure",
          "Establish public information officer",
          "Coordinate with state and federal agencies"
        ]
      }
    } else {
      return {
        content: "I've analyzed the current wildfire situation using NASA satellite data and AI-powered threat assessment. Based on my analysis, I've identified several critical insights and recommendations for emergency response.",
        toolsUsed: ["get_nasa_data_summary_enhanced", "assess_asset_threats", "rank_fire_threats"],
        dataInsights: [
          "Multiple fires detected across California",
          "Weather conditions creating high fire danger",
          "Critical infrastructure at risk",
          "Resource allocation needs identified"
        ],
        recommendations: [
          "Monitor all active fires continuously",
          "Prepare for rapid escalation",
          "Coordinate resource deployment",
          "Maintain situational awareness"
        ]
      }
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && !isProcessing) {
      processQuery(inputValue)
      setInputValue("")
    }
  }

  const handleExampleClick = (example: string) => {
    if (!isProcessing) {
      processQuery(example)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 px-4 pb-4 space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <Bot className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
            WildfireNowcast Agent Showcase
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Experience the power of AI-driven wildfire monitoring and emergency response
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              agentStatus === "active" ? "bg-green-500" :
              agentStatus === "thinking" ? "bg-yellow-500 animate-pulse" : "bg-gray-400"
            }`} />
            <span className="text-sm font-medium">
              {agentStatus === "active" ? "Agent Active" :
               agentStatus === "thinking" ? "Processing..." : "Standby"}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMessages([])}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Clear Chat
          </Button>
        </div>
      </div>

      {/* Chat Interface */}
      <Card className="h-[700px] flex flex-col">
        <CardHeader className="flex-shrink-0">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Agent Conversation
          </CardTitle>
          <CardDescription>
            Interact with the WildfireNowcast Agent
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className={`max-w-[85%] p-3 rounded-lg break-words ${
                    message.type === "user"
                      ? "bg-blue-500 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  }`}>
                    <div className="flex items-start gap-2">
                      {message.type === "agent" && (
                        <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <div className="text-sm prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                          </ReactMarkdown>
                        </div>
                        {message.toolsUsed && message.toolsUsed.length > 0 && (
                          <div className="mt-2 space-y-1">
                            <p className="text-xs font-medium">Tools Used:</p>
                            <div className="flex flex-wrap gap-1">
                              {message.toolsUsed.map((tool) => (
                                <Badge key={tool} variant="outline" className="text-xs">
                                  {tool}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        {message.dataInsights && message.dataInsights.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium mb-1">Data Insights:</p>
                            <ul className="text-xs space-y-1">
                              {message.dataInsights.map((insight, i) => (
                                <li key={i} className="flex items-start gap-1">
                                  <span className="text-green-500 mt-0.5">•</span>
                                  {insight}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {message.recommendations && message.recommendations.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium mb-1">Recommendations:</p>
                            <ul className="text-xs space-y-1">
                              {message.recommendations.map((rec, i) => (
                                <li key={i} className="flex items-start gap-1">
                                  <span className="text-blue-500 mt-0.5">→</span>
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(message.content)}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <div className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {isProcessing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Bot className="h-4 w-4" />
                    <div className="flex items-center gap-1">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span className="text-sm">Agent is thinking...</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Example Queries */}
          <div className="mb-4">
            <p className="text-sm font-medium mb-2">Try these examples:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.slice(0, 4).map((query) => (
                <Button
                  key={query}
                  variant="outline"
                  size="sm"
                  onClick={() => handleExampleClick(query)}
                  disabled={isProcessing}
                  className="text-xs hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                >
                  {query}
                </Button>
              ))}
            </div>
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask the agent about wildfire monitoring..."
              disabled={isProcessing}
              className="flex-1"
            />
            <Button type="submit" disabled={isProcessing || !inputValue.trim()}>
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default AgentShowcase
