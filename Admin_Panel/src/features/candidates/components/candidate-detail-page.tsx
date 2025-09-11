import { useParams, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Download, UserCheck, UserX, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { useCandidatesData } from '../hooks/use-candidates-data'
import { recommendations, statuses, scoreRanges } from '../data/data'
import { CandidateProfileCard } from './cards/candidate-profile-card'
import { CandidateCompetencyCard } from './cards/candidate-competency-card'
import { CandidateNextStepsCard } from './cards/candidate-next-steps-card'
import { CandidateTranscriptCard } from './cards/candidate-transcript-card'

export function CandidateDetailPage() {
  const { candidateId } = useParams({ from: '/_authenticated/candidates/$candidateId' })
  const navigate = useNavigate()
  const { candidates, loading, error } = useCandidatesData()
  
  const candidate = candidates.find(c => c.id === candidateId)
  
  if (loading) {
    return (
      <>
        <Header fixed>
          <Search />
          <div className='ms-auto flex items-center space-x-4'>
            <ThemeSwitch />
            <ConfigDrawer />
            <ProfileDropdown />
          </div>
        </Header>
        <Main>
          <div className='flex items-center justify-center h-64'>
            <div className='flex items-center space-x-2'>
              <RefreshCw className='h-6 w-6 animate-spin' />
              <span>Loading candidate...</span>
            </div>
          </div>
        </Main>
      </>
    )
  }

  if (error || !candidate) {
    return (
      <>
        <Header fixed>
          <Search />
          <div className='ms-auto flex items-center space-x-4'>
            <ThemeSwitch />
            <ConfigDrawer />
            <ProfileDropdown />
          </div>
        </Header>
        <Main>
          <div className='flex flex-col items-center justify-center h-64 space-y-4'>
            <div className='text-center'>
              <h2 className='text-xl font-semibold'>Candidate Not Found</h2>
              <p className='text-muted-foreground'>The candidate you're looking for doesn't exist.</p>
            </div>
            <Button onClick={() => navigate({ to: '/candidates' })}>
              <ArrowLeft className='mr-2 h-4 w-4' />
              Back to Candidates
            </Button>
          </div>
        </Main>
      </>
    )
  }

  const recommendation = recommendations.find(r => r.value === candidate.recommendation)
  const status = statuses.find(s => s.value === candidate.status)
  const scoreColor = candidate.overallScore >= 80 ? scoreRanges.excellent : 
                    candidate.overallScore >= 65 ? scoreRanges.good :
                    candidate.overallScore >= 50 ? scoreRanges.fair : scoreRanges.poor

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase()
  }

  return (
    <>
      <Header fixed>
        <Search />
        <div className='ms-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </Header>

      <Main>
        {/* Breadcrumbs */}
        <div className='mb-4 flex items-center space-x-2 text-sm text-muted-foreground'>
          <button 
            onClick={() => navigate({ to: '/candidates' })}
            className='hover:text-foreground transition-colors'
          >
            Candidates
          </button>
          <span>/</span>
          <span className='text-foreground'>{candidate.candidateName}</span>
        </div>

        {/* Combined Candidate Information Card */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-6">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${candidate.candidateName}`} />
                  <AvatarFallback className="text-xl">
                    {getInitials(candidate.candidateName)}
                  </AvatarFallback>
                </Avatar>
                
                {/* Contact Details */}
                <div className="space-y-1">
                  <CardTitle className="text-2xl">{candidate.candidateName}</CardTitle>
                  <p className="text-muted-foreground">{candidate.email}</p>
                  <p className="text-sm text-muted-foreground">{candidate.phone}</p>
                  <p className="text-sm font-medium text-foreground capitalize">{candidate.position}</p>
                </div>
                
                <Separator orientation="vertical" className="h-20" />
                
                {/* Interview Details */}
                <div className="space-y-2">
                  <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Interview Details</h3>
                  <div className="space-y-1">
                    <p className="text-sm">
                      <span className="font-medium">Date:</span> {new Date(candidate.interviewDate).toLocaleDateString('en-US', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                    </p>
                    <p className="text-sm">
                      <span className="font-medium">Duration:</span> {Math.floor(candidate.duration / 60)}m {Math.floor(candidate.duration % 60)}s
                    </p>
                    <p className="text-sm">
                      <span className="font-medium">Type:</span> <span className="capitalize">{candidate.interviewType}</span>
                    </p>
                  </div>
                </div>
                
                <Separator orientation="vertical" className="h-20" />
                
                {/* Quick Stats */}
                <div className="space-y-2">
                  <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">Quick Stats</h3>
                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${scoreColor.color}`}>
                        {candidate.overallScore}
                      </div>
                      <p className="text-xs text-muted-foreground">Overall Score</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-foreground">
                        {Math.round((candidate.competencyScores.empathy_compassion + 
                                   candidate.competencyScores.safety_awareness + 
                                   candidate.competencyScores.communication_skills + 
                                   candidate.competencyScores.problem_solving + 
                                   candidate.competencyScores.experience_commitment) / 5)}
                      </div>
                      <p className="text-xs text-muted-foreground">Avg Competency</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 mt-3">
                    {recommendation && (
                      <Badge className={`${recommendation.color} ${recommendation.bgColor} ${recommendation.borderColor} text-xs px-2 py-1`}>
                        <recommendation.icon className="mr-1 h-3 w-3" />
                        {recommendation.label}
                      </Badge>
                    )}
                    {status && (
                      <Badge variant="outline" className="text-xs px-2 py-1">
                        <status.icon className={`mr-1 h-3 w-3 ${status.color}`} />
                        {status.label}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  Export Report
                </Button>
                <Button variant="default" size="sm" className="bg-green-600 hover:bg-green-700">
                  <UserCheck className="mr-2 h-4 w-4" />
                  Hire
                </Button>
                <Button variant="outline" size="sm" className="text-red-600 border-red-200 hover:bg-red-50">
                  <UserX className="mr-2 h-4 w-4" />
                  Reject
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => navigate({ to: '/candidates' })}
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Two-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
          {/* Left Column - Competency Only */}
          <div className="col-span-1 lg:col-span-3 space-y-6">
            <CandidateCompetencyCard candidate={candidate} />
          </div>
          
          {/* Right Column - Transcript */}
          <div className="col-span-1 lg:col-span-4">
            <CandidateTranscriptCard candidate={candidate} />
          </div>
        </div>
      </Main>
    </>
  )
}
