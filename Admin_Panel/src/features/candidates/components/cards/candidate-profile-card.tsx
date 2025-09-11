import { format } from 'date-fns'
import { Clock, Calendar, Phone, Mail, MapPin, Award, User } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { type Candidate } from '../../data/schema'

interface CandidateProfileCardProps {
  candidate: Candidate
}

export function CandidateProfileCard({ candidate }: CandidateProfileCardProps) {
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <User className="h-5 w-5" />
          <span>Candidate Information</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Contact Information */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Contact Details</h4>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">Email</p>
                <p className="text-sm text-muted-foreground truncate">{candidate.email}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="text-sm font-medium">Phone</p>
                <p className="text-sm text-muted-foreground">{candidate.phone}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="text-sm font-medium">Position Applied</p>
                <Badge variant="outline" className="mt-1">
                  {candidate.position.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Interview Details */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Interview Details</h4>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <Calendar className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="text-sm font-medium">Interview Date</p>
                <p className="text-sm text-muted-foreground">
                  {format(new Date(candidate.interviewDate), 'EEEE, MMMM dd, yyyy')}
                </p>
                <p className="text-xs text-muted-foreground">
                  {format(new Date(candidate.interviewDate), 'h:mm a')}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="text-sm font-medium">Duration</p>
                <p className="text-sm text-muted-foreground">{formatDuration(candidate.duration)}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Award className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="text-sm font-medium">Interview Type</p>
                <Badge variant="secondary" className="mt-1">
                  {candidate.interviewType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Quick Stats</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-xl font-bold text-primary">{candidate.overallScore}</div>
              <div className="text-xs text-muted-foreground">Overall Score</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-xl font-bold text-primary">
                {Object.values(candidate.competencyScores).reduce((a, b) => a + b, 0) / 5}
              </div>
              <div className="text-xs text-muted-foreground">Avg Competency</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
