import { useState, useEffect } from 'react'
import { Search, Download, Clock, FileText, Bot, User, TrendingUp, TrendingDown, AlertTriangle, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { type Candidate, type Transcript } from '../../data/schema'
import { InterviewApiService } from '../../services/interview-api'

interface CandidateTranscriptCardProps {
  candidate: Candidate
}

// Parse real transcript data from API
const parseTranscriptData = (rawTranscript: any) => {
  if (!rawTranscript || !rawTranscript.questions || !rawTranscript.responses) {
    return []
  }

  const entries = []
  
  // Combine questions and responses
  for (let i = 0; i < rawTranscript.questions.length; i++) {
    const question = rawTranscript.questions[i]
    const response = rawTranscript.responses[i]
    
    // Add question entry
    entries.push({
      type: 'question' as const,
      speaker: 'ai' as const,
      content: question.question,
      timestamp: new Date(question.timestamp).toLocaleTimeString(),
      questionNumber: question.questionNumber,
    })
    
    // Add response entry if exists
    if (response && response.response) {
      entries.push({
        type: 'answer' as const,
        speaker: 'candidate' as const,
        content: response.response,
        timestamp: new Date(response.timestamp).toLocaleTimeString(),
        duration: response.duration || 0,
        questionNumber: response.questionNumber,
        analysis: response.analysis ? {
          sentiment: response.analysis.sentiment || 'neutral',
          keyTerms: response.analysis.keyTerms || [],
          scoreImpact: response.analysis.scoreImpact || {},
          flags: response.analysis.flags || [],
        } : undefined,
      })
    }
  }
  
  return entries
}

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
  const [transcript, setTranscript] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch real transcript data
  useEffect(() => {
    const fetchTranscript = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const rawTranscript = await InterviewApiService.fetchTranscript(candidate.id)
        if (rawTranscript) {
          // Parse the raw API data into the format expected by the UI
          const parsedEntries = parseTranscriptData(rawTranscript)
          setTranscript(parsedEntries)
        } else {
          // Fallback to sample data if no real transcript
          setTranscript(getSampleTranscript(candidate))
        }
      } catch (err) {
        console.error('Error fetching transcript:', err)
        setError('Failed to load transcript')
        // Fallback to sample data on error
        setTranscript(getSampleTranscript(candidate))
      } finally {
        setLoading(false)
      }
    }

    fetchTranscript()
  }, [candidate.id])

  const filteredTranscript = transcript.filter(entry =>
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

  if (loading) {
    return (
      <Card className="h-[600px] flex flex-col">
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
      <Card className="h-[600px] flex flex-col">
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
    <Card className="h-[600px] flex flex-col">
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
          <div>Questions: {transcript.filter(e => e.type === 'question').length}</div>
          <div>Session: {candidate.id.slice(0, 8)}...</div>
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
                        <Badge variant="outline" className="text-xs">
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
                        <Badge variant="outline" className="text-xs">
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
