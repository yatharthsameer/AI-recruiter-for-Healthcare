import { useEffect, useMemo, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import { Search, Download, Clock, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
// import { Badge } from '@/components/ui/badge'
import { type Candidate } from '../../data/schema'
import { InterviewApiService } from '../../services/interview-api'
import { TranscriptEntry } from './transcript-entry'

interface TranscriptPanelProps {
  candidate: Candidate
  selectedCompetency?: string
}

export function TranscriptPanel({ candidate, selectedCompetency }: TranscriptPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showTimestamps] = useState(true)
  const [transcript, setTranscript] = useState<any | null>(null)
  const listRef = useRef<HTMLDivElement | null>(null)
  const visualizerRef = useRef<HTMLDivElement | null>(null)
  const waveRef = useRef<WaveSurfer | null>(null)
  const regionsPluginRef = useRef<any>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [activeSegmentQ, setActiveSegmentQ] = useState<number | null>(null)
  const [activeCompetency, setActiveCompetency] = useState<string | null>(null)
  const pendingCompetencyRef = useRef<string | null>(null)

  // Fallback sample until data loads
  const sampleTranscript = [
    {
      type: 'question' as const,
      speaker: 'ai' as const,
      content: `Hi ${candidate?.candidateName?.split(' ')[0] || 'there'}, tell me about your experience as an HHA – what motivated you to choose this career path?`,
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

  type Entry = {
    type: 'question' | 'answer'
    content: string
    questionNumber?: number
    duration?: number
    timestamp?: string
    analysis?: { scoreImpact?: Record<string, number>; flags?: string[]; keyTerms?: string[]; sentiment?: string }
  }
  const entries = useMemo(() => (transcript?.entries as Entry[]) ?? (sampleTranscript as Entry[]), [transcript, sampleTranscript])
  const fullAudio = useMemo(
    () => (transcript?.fullAudio ? (transcript.fullAudio as { url?: string; segments?: { questionNumber: number; startMs: number; endMs: number }[] }) : null),
    [transcript]
  )

  const filteredTranscript = entries.filter((entry: Entry) =>
    entry.content.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // const totalDuration = entries.filter((entry) => entry.type === 'answer').reduce((sum, entry) => sum + (entry.duration || 0), 0)

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  }

  useEffect(() => {
    let mounted = true
    InterviewApiService.fetchTranscript(candidate.id).then((data) => {
      if (mounted && data) setTranscript(data)
    })
    return () => { mounted = false }
  }, [candidate.id])

  // Initialize WaveSurfer when full audio is available
  useEffect(() => {
    if (!visualizerRef.current || !fullAudio?.url) return
    // cleanup previous
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
    waveRef.current = ws
    // Wait for waveform to be ready before adding regions
    ws.on('ready', addBaseRegions)
    ws.on('play', () => setIsPlaying(true))
    ws.on('pause', () => setIsPlaying(false))
    // If there is a pending competency selection, process it now
    if (pendingCompetencyRef.current) {
      const k = pendingCompetencyRef.current
      pendingCompetencyRef.current = null
      if (k) handleCompetencyJump(k)
    }
    return () => { ws.destroy(); waveRef.current = null }
  }, [fullAudio?.url])

  // Function to highlight specific competency regions
  const highlightCompetencyRegions = (competencyKey: string) => {
    const rp = regionsPluginRef.current
    const compMap = (transcript as any)?.competencySegments as Record<string, { questionNumber: number; startMs: number; endMs: number; weight: number }[]>
    if (!rp || !compMap || !compMap[competencyKey]) return

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
    compMap[competencyKey].forEach(seg => {
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
  }

  const handlePlayAudio = (qNum?: number) => {
    if (!qNum) return
    const el = document.getElementById(`q-${qNum}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  // Helper: jump to first matching answer for a competency key
  const handleCompetencyJump = (key: string) => {
    if (!key) return
    // Prefer backend-provided competencySegments if available
    const compMap = (transcript as any)?.competencySegments as Record<string, { questionNumber: number; startMs: number; endMs: number; weight: number }[]>
    let seg: { questionNumber: number; startMs: number; endMs: number } | undefined
    if (compMap && compMap[key] && compMap[key].length > 0) {
      // Choose the highest weight or first segment
      const sorted = [...compMap[key]].sort((a, b) => (b.weight || 0) - (a.weight || 0))
      const top = sorted[0]
      seg = { questionNumber: top.questionNumber, startMs: top.startMs, endMs: top.endMs }
    } else {
      const target = entries.find((e) => e.type === 'answer' && e.analysis?.scoreImpact?.[key] && (e.analysis!.scoreImpact![key] as number) > 0)
      if (!target?.questionNumber) return
      seg = fullAudio?.segments?.find((s) => s.questionNumber === target.questionNumber)
    }
    if (seg) {
      setActiveSegmentQ(seg.questionNumber)
      if (waveRef.current) {
        waveRef.current.setTime((seg.startMs || 0) / 1000)
        waveRef.current.play()
      } else {
        // defer until waveform ready
        pendingCompetencyRef.current = key
      }
      // Ensure audio section is visible
      if (visualizerRef.current) visualizerRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
      const el = document.getElementById(`q-${seg.questionNumber}`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  // React to prop-selected competency
  useEffect(() => {
    if (!selectedCompetency) return
    handleCompetencyJump(selectedCompetency)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCompetency])

  // Also listen to global events from other components
  useEffect(() => {
    const listener = (evt: Event) => {
      const key = (evt as CustomEvent).detail?.key as string | undefined
      if (key) handleCompetencyJump(key)
    }
    window.addEventListener('competencySelect', listener as EventListener)
    return () => window.removeEventListener('competencySelect', listener as EventListener)
  }, [])

  return (
    <div className="h-full flex flex-col space-y-4">
      {/* Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Interview Transcript</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {/* Full interview audio visualizer */}
          {fullAudio?.url && (
            <div className="mb-4">
              <div ref={visualizerRef} className="w-full" />
              <div className="mt-2 flex items-center gap-2">
                <button className="text-xs px-2 py-1 rounded border" onClick={() => waveRef.current?.playPause?.()}>
                  {isPlaying ? 'Pause' : 'Play'}
                </button>
                <div className="text-xs text-muted-foreground">Full interview audio</div>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {fullAudio.segments?.map((seg) => (
                  <button
                    key={seg.questionNumber}
                    className={`text-xs px-2 py-1 rounded border ${activeSegmentQ === seg.questionNumber ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-900'}`}
                    onClick={() => {
                      setActiveSegmentQ(seg.questionNumber)
                      if (waveRef.current) {
                        waveRef.current.setTime((seg.startMs || 0) / 1000)
                        waveRef.current.play()
                      }
                      const el = document.getElementById(`q-${seg.questionNumber}`)
                      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
                    }}
                  >
                    Q{seg.questionNumber}
                  </button>
                ))}
              </div>
              
              {/* Color Legend */}
              <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
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
              </div>
            </div>
          )}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>Duration: {formatDuration(candidate.duration)}</span>
              </div>
              <div>Questions: {entries.filter((e: any) => e.type === 'question').length}</div>
              <div>Session: {candidate.id.slice(0, 8)}...</div>
            </div>
          </div>
          
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
        </CardContent>
      </Card>

      {/* Transcript Content */}
      <Card className="flex-1 overflow-hidden">
        <CardContent className="p-0 h-full">
          <ScrollArea className="h-full">
            <div className="p-6 space-y-6" ref={listRef}>
              {filteredTranscript.map((entry: Entry, index: number) => (
                <TranscriptEntry
                  key={index}
                  entry={entry}
                  showTimestamps={showTimestamps}
                  searchTerm={searchTerm}
                  selectedCompetency={selectedCompetency}
                  onPlayAudio={handlePlayAudio}
                />
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
    </div>
  )
}
