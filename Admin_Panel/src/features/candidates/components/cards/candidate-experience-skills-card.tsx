import { Briefcase } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { type Candidate } from '../../data/schema'

interface CandidateExperienceSkillsCardProps {
  candidate: Candidate
}

export function CandidateExperienceSkillsCard({ candidate }: CandidateExperienceSkillsCardProps) {
  // Enhanced dummy experience data - will be replaced with backend integration
  const workExperience = [
    {
      title: 'Home Health Aide',
      company: 'Comfort Care Services',
      duration: '2 years 3 months',
      period: '2022 - Present',
      description: 'Provided personal care and companionship to elderly clients in their homes.',
    },
    {
      title: 'Certified Nursing Assistant',
      company: 'Sunrise Senior Living',
      duration: '1 year 8 months',
      period: '2020 - 2022',
      description: 'Assisted residents with daily activities and medication management.',
    },
    {
      title: 'Caregiver',
      company: 'Family Care Solutions',
      duration: '1 year 2 months',
      period: '2019 - 2020',
      description: 'Supported individuals with disabilities in community-based settings.',
    },
  ]

  const skills = [
    { name: 'Personal Care Assistance', level: 'Expert', years: 4 },
    { name: 'Medication Management', level: 'Advanced', years: 3 },
    { name: 'Mobility Assistance', level: 'Expert', years: 4 },
    { name: 'Companionship Care', level: 'Expert', years: 5 },
    { name: 'Emergency Response', level: 'Intermediate', years: 2 },
    { name: 'Documentation', level: 'Advanced', years: 3 },
  ]


  const getSkillLevelColor = (level: string) => {
    switch (level) {
      case 'Expert':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'Advanced':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'Intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const totalExperience = workExperience.reduce((total, job) => {
    const match = job.duration.match(/(\d+)\s*years?\s*(\d+)?\s*months?/)
    if (match) {
      const years = parseInt(match[1]) || 0
      const months = parseInt(match[2]) || 0
      return total + years + (months / 12)
    }
    return total
  }, 0)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Briefcase className="h-5 w-5 text-blue-600" />
            <span>Experience & Skills</span>
          </div>
          <Badge variant="secondary" className="text-xs">
            {Math.floor(totalExperience)} years experience
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Work Experience */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Work Experience</h4>
          <div className="space-y-4">
            {workExperience.map((job, index) => (
              <div key={index} className="border-l-2 border-blue-200 pl-4 pb-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <h5 className="font-medium text-sm">{job.title}</h5>
                    <p className="text-sm text-muted-foreground">{job.company}</p>
                    <p className="text-xs text-muted-foreground">{job.description}</p>
                  </div>
                  <div className="text-right text-xs text-muted-foreground">
                    <div>{job.period}</div>
                    <div className="font-medium">{job.duration}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Core Skills */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Core Skills</h4>
          <div className="flex flex-wrap gap-2">
            {skills.map((skill, index) => (
              <Badge 
                key={index} 
                variant="outline" 
                className={`text-xs ${getSkillLevelColor(skill.level)}`}
              >
                {skill.name}
              </Badge>
            ))}
          </div>
        </div>

        {/* Availability & Preferences - Compact Single Line */}
        <div className="pt-4 border-t">
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide mb-2">Availability & Preferences</h4>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {/* Transportation */}
            {candidate.driversLicense && candidate.autoInsurance ? (
              <Badge variant="outline" className="text-green-600 border-green-200 text-xs">
                ✓ Licensed & Insured
              </Badge>
            ) : (
              <div className="flex gap-1">
                {candidate.driversLicense ? (
                  <Badge variant="outline" className="text-xs">Licensed</Badge>
                ) : (
                  <Badge variant="outline" className="text-red-600 border-red-200 text-xs">No License</Badge>
                )}
                {candidate.autoInsurance ? (
                  <Badge variant="outline" className="text-xs">Insured</Badge>
                ) : (
                  <Badge variant="outline" className="text-red-600 border-red-200 text-xs">No Insurance</Badge>
                )}
              </div>
            )}
            
            <span className="text-muted-foreground">•</span>
            
            {/* Schedule */}
            {candidate.availability && candidate.availability.length > 0 ? (
              <div className="flex flex-wrap gap-1">
                {candidate.availability.map((shift, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {shift}
                  </Badge>
                ))}
              </div>
            ) : (
              <Badge variant="secondary" className="text-xs">Schedule not specified</Badge>
            )}
            
            {candidate.weeklyHours && candidate.weeklyHours > 0 && (
              <>
                <span className="text-muted-foreground">•</span>
                <span className="text-xs text-muted-foreground">
                  {candidate.weeklyHours} hrs/week
                </span>
              </>
            )}
          </div>
        </div>

        {/* Experience Summary */}
        <div className="pt-4 border-t">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="space-y-1">
              <div className="text-lg font-bold text-blue-600">{Math.floor(totalExperience)}</div>
              <div className="text-xs text-muted-foreground">Years Experience</div>
            </div>
            <div className="space-y-1">
              <div className="text-lg font-bold text-green-600">{skills.length}</div>
              <div className="text-xs text-muted-foreground">Core Skills</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
