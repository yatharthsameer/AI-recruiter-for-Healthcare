import { Bot, User, Clock, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

interface TranscriptEntryProps {
  entry: {
    type: 'question' | 'answer' | 'system'
    speaker: 'ai' | 'candidate' | 'system'
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
  }
  showTimestamps: boolean
  searchTerm: string
}

export function TranscriptEntry({ entry, showTimestamps, searchTerm }: TranscriptEntryProps) {
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

  const formatDuration = (seconds: number) => {
    return `${seconds}s response`
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
      case 'empathetic':
        return 'text-green-600 bg-green-50'
      case 'concerning':
      case 'negative':
        return 'text-red-600 bg-red-50'
      case 'neutral':
        return 'text-blue-600 bg-blue-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getScoreImpactIcon = (impact: number) => {
    if (impact > 0) return <TrendingUp className="h-3 w-3 text-green-600" />
    if (impact < 0) return <TrendingDown className="h-3 w-3 text-red-600" />
    return null
  }

  if (entry.type === 'question') {
    return (
      <div className="flex space-x-4">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <Bot className="h-4 w-4 text-blue-600" />
          </div>
        </div>
        <div className="flex-1 space-y-2">
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-xs">
              Q{entry.questionNumber}
            </Badge>
            {showTimestamps && (
              <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>{entry.timestamp}</span>
              </div>
            )}
          </div>
          <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
              {highlightText(entry.content, searchTerm)}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (entry.type === 'answer') {
    return (
      <div className="flex space-x-4">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <User className="h-4 w-4 text-green-600" />
          </div>
        </div>
        <div className="flex-1 space-y-2">
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-xs">
              A{entry.questionNumber}
            </Badge>
            {showTimestamps && (
              <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>{entry.timestamp}</span>
              </div>
            )}
            {entry.duration && (
              <Badge variant="secondary" className="text-xs">
                {formatDuration(entry.duration)}
              </Badge>
            )}
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
            <p className="text-sm">
              {highlightText(entry.content, searchTerm)}
            </p>
          </div>

          {/* AI Analysis */}
          {entry.analysis && (
            <Card className="mt-3">
              <CardContent className="p-4">
                <div className="space-y-3">
                  {/* Sentiment */}
                  <div className="flex items-center space-x-2">
                    <Badge className={`text-xs ${getSentimentColor(entry.analysis.sentiment)}`}>
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
    )
  }

  return null
}
