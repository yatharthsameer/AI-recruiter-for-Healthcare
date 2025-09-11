import { ArrowRight, CheckSquare } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { type Candidate } from '../../data/schema'

interface CandidateNextStepsCardProps {
  candidate: Candidate
}

export function CandidateNextStepsCard({ candidate }: CandidateNextStepsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ArrowRight className="h-5 w-5 text-blue-600" />
            <span>Recommended Next Steps</span>
          </div>
          <Badge variant="secondary" className="text-xs">
            {candidate.nextSteps.length} steps
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {candidate.nextSteps.length > 0 ? (
          <>
            <ul className="space-y-3">
              {candidate.nextSteps.map((step, index) => (
                <li key={index} className="flex items-start space-x-3 group">
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>
                  </div>
                  <div className="flex-1 space-y-1">
                    <span className="text-sm leading-relaxed">{step}</span>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="sm" className="h-6 text-xs px-2">
                        <CheckSquare className="mr-1 h-3 w-3" />
                        Mark Complete
                      </Button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>

            {/* Action Buttons */}
            <div className="pt-4 border-t space-y-2">
              <Button className="w-full" size="sm">
                <CheckSquare className="mr-2 h-4 w-4" />
                Start Next Steps Process
              </Button>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="outline" size="sm" className="text-xs">
                  Schedule Follow-up
                </Button>
                <Button variant="outline" size="sm" className="text-xs">
                  Send to Manager
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-6 space-y-2">
            <div className="text-muted-foreground text-sm">No specific next steps defined</div>
            <Button variant="outline" size="sm">
              Add Next Steps
            </Button>
          </div>
        )}

        {/* Progress Indicator */}
        {candidate.nextSteps.length > 0 && (
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span>Progress</span>
              <span>0 of {candidate.nextSteps.length} completed</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: '0%' }} />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
