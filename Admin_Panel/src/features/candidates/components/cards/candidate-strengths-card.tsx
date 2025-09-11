import { CheckCircle, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { type Candidate } from '../../data/schema'

interface CandidateStrengthsCardProps {
  candidate: Candidate
}

export function CandidateStrengthsCard({ candidate }: CandidateStrengthsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <span>Strengths & Development Areas</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Strengths */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <h4 className="font-medium text-sm text-green-600 uppercase tracking-wide">Key Strengths</h4>
            <Badge variant="secondary" className="text-xs">
              {candidate.strengths.length}
            </Badge>
          </div>
          {candidate.strengths.length > 0 ? (
            <ul className="space-y-2">
              {candidate.strengths.map((strength, index) => (
                <li key={index} className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm leading-relaxed">{strength}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground italic">No specific strengths identified</p>
          )}
        </div>

        {/* Development Areas */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <h4 className="font-medium text-sm text-amber-600 uppercase tracking-wide">Development Areas</h4>
            <Badge variant="secondary" className="text-xs">
              {candidate.developmentAreas.length}
            </Badge>
          </div>
          {candidate.developmentAreas.length > 0 ? (
            <ul className="space-y-2">
              {candidate.developmentAreas.map((area, index) => (
                <li key={index} className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-amber-500 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm leading-relaxed">{area}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground italic">No specific development areas identified</p>
          )}
        </div>

        {/* Summary Stats */}
        <div className="pt-4 border-t">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="space-y-1">
              <div className="text-lg font-bold text-green-600">{candidate.strengths.length}</div>
              <div className="text-xs text-muted-foreground">Strengths</div>
            </div>
            <div className="space-y-1">
              <div className="text-lg font-bold text-amber-600">{candidate.developmentAreas.length}</div>
              <div className="text-xs text-muted-foreground">Areas to Develop</div>
            </div>
          </div>
        </div>

        {/* Assessment Note */}
        {candidate.developmentAreas.length > candidate.strengths.length && (
          <div className="flex items-start space-x-2 p-3 bg-amber-50 dark:bg-amber-950/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 dark:text-amber-200">
              <strong>Note:</strong> This candidate has more development areas than strengths. 
              Consider additional training or mentoring before placement.
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
