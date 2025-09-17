import { Target } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { type Candidate } from '../../data/schema'
import { competencyLabels, scoreRanges } from '../../data/data'

interface CandidateCompetencyCardProps {
  candidate: Candidate
  onSelect?: (competencyKey: string) => void
}

// Circular Progress Component
function CircularProgress({ value, max = 10, size = 80, strokeWidth = 8, className = "" }: {
  value: number
  max?: number
  size?: number
  strokeWidth?: number
  className?: string
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const percentage = (value / max) * 100
  const strokeDasharray = `${circumference} ${circumference}`
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  const getStrokeColor = (score: number) => {
    if (score >= 8) return '#10b981' // green-500
    if (score >= 6) return '#3b82f6' // blue-500  
    if (score >= 4) return '#f59e0b' // amber-500
    return '#ef4444' // red-500
  }

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        className="transform -rotate-90"
        width={size}
        height={size}
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="text-muted-foreground/20"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getStrokeColor(value)}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-300 ease-in-out"
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold text-foreground">
          {value}
        </span>
      </div>
    </div>
  )
}

export function CandidateCompetencyCard({ candidate, onSelect }: CandidateCompetencyCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return scoreRanges.excellent
    if (score >= 6) return scoreRanges.good
    if (score >= 4) return scoreRanges.fair
    return scoreRanges.poor
  }

  return (
    <Card className='h-full'>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Target className="h-5 w-5" />
          <span>Competency Scores</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Circular Progress Grid */}
        <div className="grid grid-cols-2 gap-6">
          {Object.entries(candidate.competencyScores).map(([key, score]) => {
            const label = competencyLabels[key as keyof typeof competencyLabels]
            
            return (
              <div
                key={key}
                className="flex flex-col items-center space-y-3 cursor-pointer"
                onClick={() => {
                  if (onSelect) onSelect(key)
                  try {
                    window.dispatchEvent(new CustomEvent('competencySelect', { detail: { key } }))
                  } catch (_err) {}
                }}
                role="button"
                aria-label={`Jump to ${label} segment`}
              >
                <CircularProgress value={score} max={10} size={70} strokeWidth={6} className="hover:opacity-90" />
                <div className="text-center">
                  <div className="text-sm font-medium leading-tight">
                    {label}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {score}/10
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap justify-center gap-3 text-xs pt-4 border-t">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>Excellent (8-10)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span>Good (6-7)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span>Fair (4-5)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>Poor (0-3)</span>
          </div>
        </div>

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
      </CardContent>
    </Card>
  )
}
