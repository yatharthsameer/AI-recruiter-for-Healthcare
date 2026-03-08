import { useState, useEffect, useRef, useCallback } from 'react'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js'
import { Search, Download, Clock, FileText, Bot, User, TrendingUp, TrendingDown, AlertTriangle, RefreshCw, Play, Pause } from 'lucide-react'
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
    rawTimestamp?: string
    duration?: number
    questionNumber?: number
    // analysis removed for cleaner UI
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
    if (!visualizerRef.current || !fullAudio?.url) {
      console.log('WaveSurfer init skipped:', { 
        hasContainer: !!visualizerRef.current, 
        hasUrl: !!fullAudio?.url,
        url: fullAudio?.url 
      })
      return
    }
    
    console.log('Initializing WaveSurfer with URL:', fullAudio.url)
    
    // Clean up existing instance
    if (waveRef.current) {
      waveRef.current.destroy()
      waveRef.current = null
    }
    
    try {
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
      
      console.log('WaveSurfer created successfully')

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
    } catch (error) {
      console.error('Error creating WaveSurfer:', error)
      return () => {
        // Cleanup function even if creation failed
        if (waveRef.current) {
          waveRef.current.destroy()
          waveRef.current = null
        }
      }
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

  // Mapping of competencies to their related questions (partial text matching)
  const competencyQuestionMapping = {
    experience_skills: [
      'Have you ever worked as a caregiver',
      'imagine you\'re finding a caregiver for',
      'how has your prior work or life experience helped you build'
    ],
    motivation: [
      'Why do you want to be a caregiver',
      'What are the most rewarding aspects'
    ],
    punctuality: [
      'Tell me about a time when being late',
      'Have you ever had to adjust your routine to ensure punctuality'
    ],
    compassion_empathy: [
      'Tell me about a time when you cared for a senior',
      'Tell me about a time when you helped a colleague or client who was struggling'
    ],
    communication_skills: [
      'If we were to ask your co-workers about you'
    ]
  }

  // Listen to competency selection and jump to first matching question
  useEffect(() => {
    // Function to find questions matching a competency
    const findQuestionsForCompetency = (competencyKey: string) => {
      const questionPatterns = competencyQuestionMapping[competencyKey as keyof typeof competencyQuestionMapping]
      if (!questionPatterns) return []

      const groupedTranscript = filterAndGroupTranscript(entries)
      const matchingGroups = groupedTranscript.filter(group => {
        const questionText = group.question.content.toLowerCase()
        return questionPatterns.some(pattern => 
          questionText.includes(pattern.toLowerCase())
        )
      })

      return matchingGroups
    }

    const handler = (evt: Event) => {
      const custom = evt as CustomEvent
      const key = (custom.detail && custom.detail.key) as string | undefined
      if (!key) return
      
      // Highlight regions for this competency (existing functionality)
      setActiveCompetency(key)
      highlightCompetencyRegions(key)
      
      // Find matching questions for this competency
      const matchingGroups = findQuestionsForCompetency(key)
      if (matchingGroups.length > 0) {
        // Jump to the first matching question
        const firstMatch = matchingGroups[0]
        const questionNumber = firstMatch.question.questionNumber
        
        if (questionNumber) {
          setActiveSegmentQ(questionNumber)
          
          // Try to seek audio if available
          const ws = waveRef.current
          if (ws && compSegments?.[key]) {
            const list = compSegments[key]
            const best = [...list].sort((a, b) => (b.weight || 0) - (a.weight || 0))[0]
            if (best) {
              ws.setTime((best.startMs || 0) / 1000)
              ws.play()
            }
          }
          
          // Scroll to the question in the transcript
          const questionElement = document.querySelector(`[data-question-number="${questionNumber}"]`)
          if (questionElement) {
            questionElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }
      }
      
      // Fallback to original behavior if no text matches found
      if (matchingGroups.length === 0) {
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
    }
    window.addEventListener('competencySelect', handler as EventListener)
    return () => window.removeEventListener('competencySelect', handler as EventListener)
  }, [compSegments, highlightCompetencyRegions, entries])

  // Function to handle clicking on transcript entries
  const handleTranscriptEntryClick = useCallback((entry: any) => {
    console.log('🎯 Transcript entry clicked:', {
      timestamp: entry.timestamp,
      content: entry.content.substring(0, 50) + '...',
      type: entry.type,
      questionNumber: entry.questionNumber
    })
    
    const ws = waveRef.current
    const rp = regionsPluginRef.current
    
    console.log('WaveSurfer instance:', ws)
    console.log('Regions plugin:', rp)
    console.log('Available entries count:', entries.length)
    console.log('Available audio segments:', fullAudio?.segments?.length || 0)
    
    if (!ws || !entry.timestamp) {
      console.log('Missing WaveSurfer or timestamp')
      return
    }

    try {
      // 1) Compute start (this entry) and end (next entry) from raw ISO timestamps
      const currentIndex = entries.findIndex(e => e.timestamp === entry.timestamp && e.content === entry.content)
      if (currentIndex === -1) return
      const startRaw = entries[currentIndex].rawTimestamp || entries[currentIndex].timestamp
      const endRaw = entries[currentIndex + 1]?.rawTimestamp || entries[currentIndex + 1]?.timestamp

      const startMs = startRaw ? new Date(startRaw).getTime() : NaN
      const firstRaw = entries[0]?.rawTimestamp || entries[0]?.timestamp
      const baseMs = firstRaw ? new Date(firstRaw).getTime() : NaN
      let seekTime = isNaN(startMs) || isNaN(baseMs) ? 0 : (startMs - baseMs) / 1000

      let endTime = seekTime + 10
      if (endRaw) {
        const endAbs = new Date(endRaw).getTime()
        if (!isNaN(endAbs) && !isNaN(baseMs)) {
          endTime = (endAbs - baseMs) / 1000
        }
      }

      // Clamp within duration
      const duration = ws.getDuration() || 0
      seekTime = Math.max(0, Math.min(duration, seekTime))
      endTime = Math.max(seekTime, Math.min(duration, endTime))

      console.log('Calculated times (raw ISO):', { seekTime, endTime, duration })

      // 2) Seek using absolute seconds (no ratios)
      if (typeof (ws as any).setTime === 'function') {
        ;(ws as any).setTime(seekTime)
      } else {
        ws.seekTo(seekTime / Math.max(1, duration))
      }
      
      // Create and highlight the region for this message
      if (rp) {
        console.log('Creating regions...')
        // Clear existing regions
        rp.clearRegions()
        
        // Optionally add base segments if available (commented to keep minimal)

        // Highlight the current message region (from current timestamp to next timestamp)
        if (endTime > seekTime) {
          console.log('Adding highlight region:', { start: seekTime, end: endTime })
          rp.addRegion({ 
            start: seekTime, 
            end: endTime, 
            color: 'rgba(59, 130, 246, 0.3)', // Blue highlight
            drag: false, 
            resize: false 
          })
        }
      } else {
        console.log('No regions plugin available')
      }

      // Try to auto-play, but don't worry if it fails due to browser restrictions
      console.log('Current playing state:', isPlaying)
      console.log('WaveSurfer ready state:', ws.isReady)
      console.log('WaveSurfer duration:', ws.getDuration())
      
      // If already playing, just continue playing from the new position
      if (isPlaying) {
        console.log('Already playing, continuing from new position')
        // Audio will continue playing from the seeked position
      } else {
        // Try to start playback, but handle autoplay restrictions gracefully
        console.log('Attempting to start playback...')
        try {
          const playPromise = ws.play()
          console.log('Play promise:', playPromise)
          
          if (playPromise && typeof playPromise.then === 'function') {
            playPromise
              .then(() => {
                console.log('✅ Audio started successfully via auto-play')
                setIsPlaying(true)
              })
              .catch((error) => {
                console.log('⚠️ Auto-play blocked by browser:', error.message)
                console.log('💡 User can click the Play button to start audio from the highlighted region')
                // Don't set isPlaying since autoplay was blocked
                // The seek position is set, so when user clicks Play, it will start from the right spot
              })
          } else {
            // Older WaveSurfer version - assume it worked
            console.log('✅ Play called (older WaveSurfer version)')
            setIsPlaying(true)
          }
        } catch (playError) {
          console.log('⚠️ Play attempt failed:', playError.message)
          console.log('💡 User can click the Play button to start audio')
        }
      }

    } catch (error) {
      console.error('Error seeking to timestamp:', error)
    }
  }, [entries, fullAudio?.segments, isPlaying])

  // Helper function to filter and group transcript entries
  const filterAndGroupTranscript = (entries: Entry[]) => {
    // Filter out system messages and initial exchanges before the first real question
    const filteredEntries = entries.filter((entry, index) => {
      // Skip system messages
      if (entry.type === 'system') return false
      
      // Skip initial exchanges that aren't real interview questions
      // Look for the first substantial question (usually contains "caregiver" or similar interview content)
      if (entry.type === 'question') {
        const content = entry.content.toLowerCase()
        // Skip intro messages like "Hi, I'm CareBot" or "Ready?"
        if (content.includes('carebot') || content.includes('ready') || content.length < 30) {
          return false
        }
      }
      
      // Skip single word answers like "Yes", "Bye" that come before real questions
      if (entry.type === 'answer' && entry.content.trim().split(' ').length <= 2) {
        // Check if this answer comes before the first real question
        const nextQuestionIndex = entries.findIndex((e, i) => 
          i > index && e.type === 'question' && e.content.length > 30
        )
        const hasRealQuestionBefore = entries.slice(0, index).some(e => 
          e.type === 'question' && e.content.length > 30
        )
        if (!hasRealQuestionBefore && nextQuestionIndex !== -1) {
          return false
        }
      }
      
      return true
    })

    // Group questions with their corresponding answers
    const grouped = []
    let currentQuestion = null
    let currentAnswers = []

    filteredEntries.forEach(entry => {
      if (entry.type === 'question') {
        // Save previous group if exists
        if (currentQuestion) {
          grouped.push({
            question: currentQuestion,
            answers: [...currentAnswers]
          })
        }
        // Start new group
        currentQuestion = entry
        currentAnswers = []
      } else if (entry.type === 'answer' && currentQuestion) {
        currentAnswers.push(entry)
      }
    })

    // Add the last group
    if (currentQuestion) {
      grouped.push({
        question: currentQuestion,
        answers: [...currentAnswers]
      })
    }

    return grouped
  }

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

  // Group and filter transcript
  const groupedTranscript = filterAndGroupTranscript(entries)
  const filteredGroupedTranscript = groupedTranscript.filter(group => 
    group.question.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    group.answers.some(answer => answer.content.toLowerCase().includes(searchTerm.toLowerCase()))
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
    <Card className="h-[700px] flex flex-col overflow-hidden">
      <CardHeader className="flex-shrink-0 pb-3">
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
          <div>Questions: {groupedTranscript.length}</div>
          <div>Session: {candidate.id.slice(0, 8)}...</div>
        </div>

        {/* Full Interview Audio */}
        {fullAudio?.url && (
          <div className="mt-2">
            {/* Hidden controller audio to enable precise seeks while using visualizer for UI */}
            <audio ref={playerRef} data-full src={fullAudio.url} style={{ display: 'none' }} />
            {/* WaveSurfer visualizer with play button */}
            <div className="flex items-center gap-2">
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => waveRef.current?.playPause()}
                className="flex-shrink-0"
              >
                {isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
              </Button>
              <div id="full-audio-player" className="flex-1 min-h-[60px]" ref={visualizerRef} />
            </div>
          </div>
        )}
        
        {/* Search */}
        <div className="relative mt-2">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search in transcript..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 h-8"
            size="sm"
          />
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0 min-h-0">
        <ScrollArea className="h-full px-6 pb-6 pt-2">
          <div className="space-y-3">
            {filteredGroupedTranscript.map((group, index) => (
              <div key={index} className="border rounded-lg overflow-hidden" data-question-number={group.question.questionNumber}>
                {/* Question Section */}
                <div 
                  className="bg-blue-50 dark:bg-blue-950/30 border-b border-blue-200 dark:border-blue-800 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-950/50 transition-colors"
                  onClick={() => handleTranscriptEntryClick(group.question)}
                  title="Click to jump to this part of the audio"
                >
                  <div className="flex space-x-3 p-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                        <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      </div>
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs cursor-pointer" onClick={(e) => {
                          e.stopPropagation()
                          seekFullAudioToQuestion(group.question.questionNumber || 0)
                        }}>
                          Q{group.question.questionNumber}
                        </Badge>
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{group.question.timestamp}</span>
                        </div>
                      </div>
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                        {highlightText(group.question.content, searchTerm)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Answers Section */}
                <div className="bg-white dark:bg-gray-950">
                  {group.answers.map((answer, answerIndex) => (
                    <div 
                      key={answerIndex}
                      className="border-b border-gray-100 dark:border-gray-800 last:border-b-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors"
                      onClick={() => handleTranscriptEntryClick(answer)}
                      title="Click to jump to this part of the audio"
                    >
                      <div className="flex space-x-3 p-3">
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                            <User className="h-4 w-4 text-green-600 dark:text-green-400" />
                          </div>
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center space-x-2">
                            <Badge variant="outline" className="text-xs cursor-pointer" onClick={(e) => {
                              e.stopPropagation()
                              seekFullAudioToQuestion(answer.questionNumber || 0)
                            }}>
                              A{answer.questionNumber}
                            </Badge>
                            <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span>{answer.timestamp}</span>
                            </div>
                            {answer.duration && (
                              <Badge variant="secondary" className="text-xs">
                                {answer.duration}s response
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-900 dark:text-gray-100">
                            {highlightText(answer.content, searchTerm)}
                          </p>
                          {answer.audioUrl && (
                            <div className="mt-3">
                              <audio controls src={answer.audioUrl} className="w-full" />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            
            {filteredGroupedTranscript.length === 0 && searchTerm && (
              <div className="text-center py-8 text-muted-foreground">
                No results found for "{searchTerm}"
              </div>
            )}

            {filteredGroupedTranscript.length === 0 && !searchTerm && entries.length > 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No interview questions found. The transcript may contain only system messages.
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
