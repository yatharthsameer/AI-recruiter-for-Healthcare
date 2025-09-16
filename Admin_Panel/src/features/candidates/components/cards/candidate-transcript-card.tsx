import { useState, useEffect, useRef, useCallback } from 'react'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import { Search, Download, Clock, FileText, Bot, User, TrendingUp, TrendingDown, AlertTriangle, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { type Candidate } from '../../data/schema'
import { InterviewApiService } from '../../services/interview-api'

interface CandidateTranscriptCardProps {
  candidate: Candidate
}

// Note: The InterviewApiService already transforms transcript to entries[]

// Fallback sample data if API fails
const getSampleTranscript = (candidate: Candidate) => [
  {
    type: 'question' as const,
    speaker: 'ai' as const,
    content: `Hi ${candidate.candidateName.split(' ')[0]}, tell me about your experience as an HHA – what motivated you to choose this career path?`,
    timestamp: '14:02:15',
    questionNumber: 1,
  },
  {
    type: 'answer' as const,
    speaker: 'candidate' as const,
    content: 'I have been involved in uh care giving for a long time now. Uh I had a grandmother who actually passed away uh because I couldn\'t care for her. So this motivated me to pursue this career so that I could provide a better care giving experience uh for a lot of different adults around me.',
    timestamp: '14:02:32',
    duration: 17,
    questionNumber: 1,
    analysis: {
      sentiment: 'empathetic',
      keyTerms: ['grandmother', 'care giving', 'motivated', 'experience'],
      scoreImpact: { empathy: 2, communication: -1 },
      flags: ['personal motivation', 'lacks detail'],
    },
  },
  {
    type: 'question' as const,
    speaker: 'ai' as const,
    content: 'Tell me about a time a client was difficult or uncooperative. How did you handle it?',
    timestamp: '14:03:45',
    questionNumber: 2,
  },
  {
    type: 'answer' as const,
    speaker: 'candidate' as const,
    content: 'Yeah, so I had a client who was 82 years of age, uh who was very uncooperative. I mean, she could not understand what I was saying. She was suffering from dementia as well. Uh and she refused to take her medicine sometimes. But it was a good experience that I was able to help her uh get get an understanding of what is important for her, get her to take her medicines and stuff.',
    timestamp: '14:04:02',
    duration: 23,
    questionNumber: 2,
    analysis: {
      sentiment: 'neutral',
      keyTerms: ['client', 'dementia', 'medicine', 'understanding'],
      scoreImpact: { empathy: 1, problem_solving: 1, communication: -1 },
      flags: ['lacks specific strategies', 'vague response'],
    },
  },
  {
    type: 'question' as const,
    speaker: 'ai' as const,
    content: 'Imagine a client refuses their medication; how would you approach that situation, ensuring their safety and well-being?',
    timestamp: '14:05:15',
    questionNumber: 3,
  },
  {
    type: 'answer' as const,
    speaker: 'candidate' as const,
    content: 'Yeah so basically I\'ll have to convince her that this is very important for her and ensure that she takes her medication. I might feed her the medication inside another food or inside what she likes so that she won\'t have to take it directly. I mean but I have to convince her that she has to take it.',
    timestamp: '14:05:28',
    duration: 18,
    questionNumber: 3,
    analysis: {
      sentiment: 'concerning',
      keyTerms: ['convince', 'medication', 'food', 'directly'],
      scoreImpact: { safety: -3, problem_solving: -2 },
      flags: ['ethical concern', 'unsafe practice', 'covert medication'],
    },
  },
]

export function CandidateTranscriptCard({ candidate }: CandidateTranscriptCardProps) {
  const [searchTerm, setSearchTerm] = useState('')
  type Entry = {
    type: 'question' | 'answer'
    speaker: 'ai' | 'candidate'
    content: string
    timestamp: string
    duration?: number
    questionNumber?: number
    analysis?: {
      sentiment: string
      keyTerms: string[]
      scoreImpact: Record<string, number>
      flags?: string[]
    }
    audioUrl?: string
  }
  const [entries, setEntries] = useState<Entry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fullAudio, setFullAudio] = useState<{ url: string; segments: { questionNumber: number; startMs: number; endMs: number }[] } | null>(null)
  const [compSegments, setCompSegments] = useState<Record<string, { questionNumber: number; startMs: number; endMs: number; weight: number }[]> | null>(null)
  const [activeSegmentQ, setActiveSegmentQ] = useState<number | null>(null)
  const [_activeCompetency, setActiveCompetency] = useState<string | null>(null)
  const visualizerRef = useRef<HTMLDivElement | null>(null)
  const playerRef = useRef<HTMLAudioElement | null>(null)
  const waveRef = useRef<WaveSurfer | null>(null)
  const regionsPluginRef = useRef<{ addRegion: (opts: any) => void; clearRegions: () => void } | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)

  // Initialize wavesurfer on mount when fullAudio is ready
  useEffect(() => {
    if (!visualizerRef.current || !fullAudio?.url) return
    // Clean up existing instance
    if (waveRef.current) {
      waveRef.current.destroy()
      waveRef.current = null
    }
    const ws = WaveSurfer.create({
      container: visualizerRef.current,
      waveColor: '#a3bffa',
      progressColor: '#2563eb',
      cursorColor: '#111827',
      height: 80,
      responsive: true,
      interact: true,
      url: fullAudio.url,
    })
    waveRef.current = ws

    // Add base regions after waveform is ready
    const addBaseRegions = () => {
      try {
        type RegionController = { addRegion: (opts: { start: number; end: number; color?: string; drag?: boolean; resize?: boolean }) => void; clearRegions: () => void }
        const rp = ws.registerPlugin(RegionsPlugin.create()) as unknown as RegionController
        regionsPluginRef.current = rp
        
        // Only base regions for all spoken answers (light gray)
        if (rp && fullAudio?.segments?.length) {
          fullAudio.segments.forEach(seg => {
            const start = (seg.startMs || 0) / 1000
            const end = (seg.endMs || 0) / 1000
            if (end > start) {
              rp.addRegion({ 
                start, 
                end, 
                color: 'rgba(107,114,128,0.15)', 
                drag: false, 
                resize: false 
              })
            }
          })
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.debug('Regions plugin setup failed:', err)
      }
    }

    // Wait for waveform to be ready before adding regions
    ws.on('ready', addBaseRegions)
    ws.on('play', () => setIsPlaying(true))
    ws.on('pause', () => setIsPlaying(false))
    
    return () => {
      ws.destroy()
      waveRef.current = null
    }
  }, [fullAudio?.url, compSegments, fullAudio?.segments])

  // Function to highlight specific competency regions
  const highlightCompetencyRegions = useCallback((competencyKey: string) => {
    const rp = regionsPluginRef.current
    if (!rp || !compSegments || !compSegments[competencyKey]) return

    // Clear existing regions and re-add base regions
    rp.clearRegions()
    
    // Re-add base regions
    if (fullAudio?.segments?.length) {
      fullAudio.segments.forEach(seg => {
        const start = (seg.startMs || 0) / 1000
        const end = (seg.endMs || 0) / 1000
        if (end > start) {
          rp.addRegion({ 
            start, 
            end, 
            color: 'rgba(107,114,128,0.15)', 
            drag: false, 
            resize: false 
          })
        }
      })
    }

    // Add colored regions for selected competency
    const competencyColors: Record<string, string> = {
      empathy_compassion: 'rgba(37, 99, 235, 0.4)',      // Blue
      experience_commitment: 'rgba(16, 185, 129, 0.4)',   // Green
      problem_solving: 'rgba(234, 179, 8, 0.4)',          // Yellow
      safety_awareness: 'rgba(244, 63, 94, 0.4)',         // Red
      communication_skills: 'rgba(139, 92, 246, 0.4)'     // Purple
    }
    
    const color = competencyColors[competencyKey] || 'rgba(107, 114, 128, 0.4)'
    compSegments[competencyKey].forEach(seg => {
      const start = (seg.startMs || 0) / 1000
      const end = (seg.endMs || 0) / 1000
      if (end > start) {
        rp.addRegion({ 
          start, 
          end, 
          color, 
          drag: false, 
          resize: false 
        })
      }
    })
  }, [compSegments, fullAudio?.segments])

  // Listen to competency selection and jump to first matching answer
  useEffect(() => {
    const handler = (evt: Event) => {
      const custom = evt as CustomEvent
      const key = (custom.detail && custom.detail.key) as string | undefined
      if (!key) return
      
      // Highlight regions for this competency
      setActiveCompetency(key)
      highlightCompetencyRegions(key)
      
      const list = compSegments?.[key]
      if (!list || list.length === 0) return
      // Choose highest-weighted segment
      const best = [...list].sort((a, b) => (b.weight || 0) - (a.weight || 0))[0]
      if (!best) return
      setActiveSegmentQ(best.questionNumber)
      const ws = waveRef.current
      if (ws) {
        ws.setTime((best.startMs || 0) / 1000)
        ws.play()
      }
      const el = document.getElementById(`q-${best.questionNumber}`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    window.addEventListener('competencySelect', handler as EventListener)
    return () => window.removeEventListener('competencySelect', handler as EventListener)
  }, [compSegments, highlightCompetencyRegions])

  // Fetch real transcript data
  useEffect(() => {
    const fetchTranscript = async () => {
      try {
        setLoading(true)
        setError(null)
        
        type TransformedTranscript = { entries: Entry[]; fullAudio?: { url?: string; segments?: { questionNumber: number; startMs: number; endMs: number }[] }; competencySegments?: Record<string, { questionNumber: number; startMs: number; endMs: number; weight: number }[]> }
        const transformed = await InterviewApiService.fetchTranscript(candidate.id) as unknown as TransformedTranscript | null
        if (transformed && Array.isArray(transformed.entries)) {
          setEntries((transformed.entries || []) as Entry[])
          // Try to get full audio from raw endpoint as well
          const fa = transformed.fullAudio
          if (fa?.url) {
            setFullAudio({ url: fa.url, segments: (fa.segments || []) })
          }
          const cs = transformed.competencySegments
          if (cs && typeof cs === 'object') setCompSegments(cs)
        } else {
          // Fallback to sample data if no real transcript
          // Normalize sample scoreImpact to Record<string, number>
          const rawSample = getSampleTranscript(candidate) as unknown[]
          const normalized: Entry[] = []
          for (const item of rawSample) {
            const entry = item as { type: string; analysis?: { scoreImpact?: Record<string, number | undefined>; [k: string]: unknown } } & Record<string, unknown>
            if (entry.type === 'answer' && entry.analysis) {
              const raw = (entry.analysis?.scoreImpact || {}) as Record<string, number | undefined>
              const norm: Record<string, number> = {}
              Object.entries(raw).forEach(([k, v]) => {
                if (typeof v === 'number') norm[k] = v
              })
              normalized.push({
                ...(entry as unknown as Entry),
                analysis: {
                  ...(entry.analysis as Record<string, unknown>),
                  scoreImpact: norm
                }
              } as unknown as Entry)
            } else {
              normalized.push(entry as unknown as Entry)
            }
          }
          // Final cast after normalization
          setEntries(normalized as Entry[])
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('Error fetching transcript:', err)
        setError('Failed to load transcript')
        // Fallback to sample data on error (normalize types)
        const sample = (getSampleTranscript(candidate) as unknown[]).map((e: unknown) => {
          const entryObj = e as { type?: string; analysis?: { scoreImpact?: Record<string, unknown> } } & Record<string, unknown>
          if (entryObj.type === 'answer' && entryObj.analysis) {
            const norm: Record<string, number> = {}
            Object.entries((entryObj.analysis.scoreImpact || {}) as Record<string, unknown>).forEach(([k, v]) => {
              if (typeof v === 'number') norm[k] = v
            })
            return { ...entryObj, analysis: { ...entryObj.analysis, scoreImpact: norm } }
          }
          return entryObj
        }) as Entry[]
        setEntries(sample)
      } finally {
        setLoading(false)
      }
    }

    fetchTranscript()
  }, [candidate.id, candidate])

  const filteredTranscript = entries.filter((entry: Entry) =>
    entry.content.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  }

  const highlightText = (text: string, term: string) => {
    if (!term) return text
    
    const regex = new RegExp(`(${term})`, 'gi')
    const parts = text.split(regex)
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
          {part}
        </mark>
      ) : part
    )
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
      case 'empathetic':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'concerning':
      case 'negative':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'neutral':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getScoreImpactIcon = (impact: number) => {
    if (impact > 0) return <TrendingUp className="h-3 w-3 text-green-600" />
    if (impact < 0) return <TrendingDown className="h-3 w-3 text-red-600" />
    return null
  }

  const seekFullAudioToQuestion = (questionNumber: number) => {
    if (!fullAudio) return
    const seg = fullAudio.segments.find((s) => s.questionNumber === questionNumber)
    if (!seg) return
    setActiveSegmentQ(questionNumber)
    // Scroll to entry
    const el = document.getElementById(`q-${questionNumber}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  if (loading) {
    return (
      <Card className="h-full flex flex-col">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Interview Transcript</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-6 w-6 animate-spin" />
            <span>Loading transcript...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="h-full flex flex-col">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Interview Transcript</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto" />
            <p className="text-red-600">{error}</p>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => window.location.reload()}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Interview Transcript</span>
          </CardTitle>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
        
        {/* Transcript Info */}
        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <div className="flex items-center space-x-1">
            <Clock className="h-4 w-4" />
            <span>Duration: {formatDuration(candidate.duration)}</span>
          </div>
          <div>Questions: {entries.filter(e => e.type === 'question').length}</div>
          <div>Session: {candidate.id.slice(0, 8)}...</div>
        </div>

        {/* Full Interview Audio */}
        {fullAudio?.url && (
          <div className="mt-3">
            {/* Hidden controller audio to enable precise seeks while using visualizer for UI */}
            <audio ref={playerRef} data-full src={fullAudio.url} style={{ display: 'none' }} />
            {/* WaveSurfer visualizer */}
            <div id="full-audio-player" className="w-full" ref={visualizerRef} />
            <div className="mt-2 flex items-center gap-2">
              <Button size="sm" onClick={() => waveRef.current?.playPause()}>
                {isPlaying ? 'Pause' : 'Play'}
              </Button>
              <div className="text-xs text-muted-foreground">Full interview audio</div>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {fullAudio.segments?.map((seg) => (
                <button
                  key={seg.questionNumber}
                  className={`text-xs px-2 py-1 rounded border ${activeSegmentQ === seg.questionNumber ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-900'}`}
                  onClick={() => {
                    setActiveSegmentQ(seg.questionNumber)
                    const ws = waveRef.current
                    if (ws) {
                      ws.setTime((seg.startMs || 0) / 1000)
                      ws.play()
                    }
                  }}
                >
                  Q{seg.questionNumber}
                </button>
              ))}
            </div>
            
            {/* Color Legend */}
            {/* <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Waveform Color Legend:</div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(107,114,128,0.4)' }}></div>
                  <span>All Speech</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(37, 99, 235, 0.4)' }}></div>
                  <span>Empathy & Compassion</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(16, 185, 129, 0.4)' }}></div>
                  <span>Experience & Commitment</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(234, 179, 8, 0.4)' }}></div>
                  <span>Problem Solving</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(244, 63, 94, 0.4)' }}></div>
                  <span>Safety Awareness</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(139, 92, 246, 0.4)' }}></div>
                  <span>Communication Skills</span>
                </div>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                💡 Click on competency scores to highlight specific segments in the waveform
              </div>
            </div> */}
          </div>
        )}
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search in transcript..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6 pb-6">
          <div className="space-y-6">
            {filteredTranscript.map((entry, index) => (
              <div key={index}>
                {entry.type === 'question' ? (
                  <div className="flex space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                        <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      </div>
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs cursor-pointer" onClick={() => seekFullAudioToQuestion(entry.questionNumber || 0)}>
                          Q{entry.questionNumber}
                        </Badge>
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{entry.timestamp}</span>
                        </div>
                      </div>
                      <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
                        <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                          {highlightText(entry.content, searchTerm)}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                        <User className="h-4 w-4 text-green-600 dark:text-green-400" />
                      </div>
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs cursor-pointer" onClick={() => seekFullAudioToQuestion(entry.questionNumber || 0)}>
                          A{entry.questionNumber}
                        </Badge>
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{entry.timestamp}</span>
                        </div>
                        {entry.duration && (
                          <Badge variant="secondary" className="text-xs">
                            {entry.duration}s response
                          </Badge>
                        )}
                      </div>
                      
                      <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg border">
                        <p className="text-sm">
                          {highlightText(entry.content, searchTerm)}
                        </p>
                        {entry.audioUrl && (
                          <div className="mt-3">
                            <audio controls src={entry.audioUrl} className="w-full" />
                          </div>
                        )}
                      </div>

                      {/* AI Analysis */}
                      {entry.analysis && (
                        <Card className="mt-3 border-l-4 border-l-blue-500">
                          <CardContent className="p-4">
                            <div className="space-y-3">
                              {/* Sentiment */}
                              <div className="flex items-center space-x-2">
                                <Badge className={`text-xs border ${getSentimentColor(entry.analysis.sentiment)}`}>
                                  {entry.analysis.sentiment}
                                </Badge>
                                {entry.analysis.flags && entry.analysis.flags.some(flag => 
                                  flag.includes('concern') || flag.includes('unsafe') || flag.includes('ethical')
                                ) && (
                                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                                )}
                              </div>

                              {/* Key Terms */}
                              {entry.analysis.keyTerms.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  {entry.analysis.keyTerms.map((term, index) => (
                                    <Badge key={index} variant="outline" className="text-xs">
                                      {term}
                                    </Badge>
                                  ))}
                                </div>
                              )}

                              {/* Score Impact */}
                              {Object.keys(entry.analysis.scoreImpact).length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                  {Object.entries(entry.analysis.scoreImpact).map(([competency, impact]) => (
                                    <div key={competency} className="flex items-center space-x-1 text-xs">
                                      {getScoreImpactIcon(impact)}
                                      <span className="capitalize">
                                        {competency.replace('_', ' ')}: {impact > 0 ? '+' : ''}{impact}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Flags */}
                              {entry.analysis.flags && entry.analysis.flags.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  {entry.analysis.flags.map((flag, index) => (
                                    <Badge 
                                      key={index} 
                                      variant={flag.includes('concern') || flag.includes('unsafe') ? 'destructive' : 'secondary'}
                                      className="text-xs"
                                    >
                                      {flag}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {filteredTranscript.length === 0 && searchTerm && (
              <div className="text-center py-8 text-muted-foreground">
                No results found for "{searchTerm}"
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
