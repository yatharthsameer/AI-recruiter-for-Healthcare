import { useState } from 'react'
import { Search, Download, Clock, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { type Candidate } from '../../data/schema'
import { TranscriptEntry } from './transcript-entry'

interface TranscriptPanelProps {
  candidate: Candidate
}

export function TranscriptPanel({ candidate }: TranscriptPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showTimestamps, setShowTimestamps] = useState(true)

  // Sample transcript data - in real implementation, this would come from the backend
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

  const filteredTranscript = sampleTranscript.filter(entry =>
    entry.content.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totalDuration = sampleTranscript
    .filter(entry => entry.type === 'answer')
    .reduce((sum, entry) => sum + (entry.duration || 0), 0)

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  }

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
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>Duration: {formatDuration(candidate.duration)}</span>
              </div>
              <div>Questions: {sampleTranscript.filter(e => e.type === 'question').length}</div>
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
            <div className="p-6 space-y-6">
              {filteredTranscript.map((entry, index) => (
                <TranscriptEntry
                  key={index}
                  entry={entry}
                  showTimestamps={showTimestamps}
                  searchTerm={searchTerm}
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
