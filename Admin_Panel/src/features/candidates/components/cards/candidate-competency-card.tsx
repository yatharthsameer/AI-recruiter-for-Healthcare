import { Target } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { type Candidate } from '../../data/schema'
import { competencyLabels, scoreRanges } from '../../data/data'

interface CandidateCompetencyCardProps {
  candidate: Candidate
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

export function CandidateCompetencyCard({ candidate }: CandidateCompetencyCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return scoreRanges.excellent
    if (score >= 6) return scoreRanges.good
    if (score >= 4) return scoreRanges.fair
    return scoreRanges.poor
  }

  return (
    <Card>
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
              <div key={key} className="flex flex-col items-center space-y-3">
                <CircularProgress value={score} max={10} size={70} strokeWidth={6} />
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
      </CardContent>
    </Card>
  )
}
