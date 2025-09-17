import { useState } from 'react'
import { useParams, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Download, UserCheck, UserX, RefreshCw, FileText, CalendarDays } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  const [activeTab, setActiveTab] = useState('experience')

  type DocumentItem = {
    key: string
    label: string
    expiry?: string | null
  }

  // Placeholder docs data; wire these to real fields when available
  const documentItems: DocumentItem[] = [
    { key: 'driving_license', label: 'Driving license', expiry: '2026-03-15' }, // valid
    { key: 'auto_insurance', label: 'Auto insurance', expiry: '2025-07-31' }, // expired
    { key: 'i9_form', label: 'I-9 form', expiry: '2025-11-01' }, // valid
    { key: 'tb_test', label: 'TB test result', expiry: '2025-05-10' }, // expired
  ]

  const getDocStatus = (expiry?: string | null) => {
    if (!expiry) return { text: 'Missing', color: 'border-muted text-muted-foreground', badgeVariant: 'secondary' as const, extra: '' }
    const exp = new Date(expiry)
    const now = new Date()
    if (isNaN(exp.getTime())) return { text: 'Unknown', color: 'border-muted text-muted-foreground', badgeVariant: 'secondary' as const, extra: '' }
    const expired = exp < now
    return expired
      ? { text: 'Expired', color: 'text-red-600 border-red-200', badgeVariant: 'outline' as const, extra: `on ${exp.toLocaleDateString()}` }
      : { text: 'Valid', color: 'text-green-600 border-green-200', badgeVariant: 'outline' as const, extra: `until ${exp.toLocaleDateString()}` }
  }
  
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
                <Avatar className="h-14 w-14">
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
                        {Math.round((candidate.competencyScores.experience_skills + 
                                   candidate.competencyScores.motivation + 
                                   candidate.competencyScores.punctuality + 
                                   candidate.competencyScores.compassion_empathy + 
                                   candidate.competencyScores.communication) / 5)}
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

        {/* Tabs + Two-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-7 gap-6 h-[calc(100vh-380px)]">
          {/* Left Column */}
          <div className={`col-span-1 ${activeTab === 'scores' ? 'lg:col-span-3' : 'lg:col-span-7'} flex flex-col h-full`}>
            {/* Top general info card already rendered above. Now tabbed content */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full h-full flex flex-col">
              <TabsList>
                <TabsTrigger value="experience">Experience & Skills</TabsTrigger>
                <TabsTrigger value="docs">
                  <span className="flex items-center gap-1"><FileText className="h-4 w-4" /> Docs</span>
                </TabsTrigger>
                <TabsTrigger value="availability">
                  <span className="flex items-center gap-1"><CalendarDays className="h-4 w-4" /> Availability</span>
                </TabsTrigger>
                <TabsTrigger value="scores">Scores</TabsTrigger>
              </TabsList>

              <TabsContent value="experience" className="mt-4 flex-1 overflow-hidden">
                <div className="space-y-6 h-full overflow-auto">
                  <CandidateProfileCard candidate={candidate} />
                  <CandidateNextStepsCard candidate={candidate} />
                </div>
              </TabsContent>

              <TabsContent value="docs" className="mt-4 flex-1 overflow-hidden">
                <Card className="h-full flex flex-col">
                  <CardHeader className="flex-shrink-0">
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" /> Documents
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-auto space-y-3">
                    {documentItems.map((doc) => {
                      const status = getDocStatus(doc.expiry)
                      return (
                        <div key={doc.key} className="flex items-center justify-between rounded-lg border p-3">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">{doc.label}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={status.badgeVariant} className={`text-xs ${status.color}`}>
                              {status.text}
                            </Badge>
                            {status.extra && (
                              <span className="text-xs text-muted-foreground">{status.extra}</span>
                            )}
                          </div>
                        </div>
                      )
                    })}
                    <p className="text-xs text-muted-foreground">Connect these to real expiry dates to show Valid/Expired automatically.</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="availability" className="mt-4 flex-1 overflow-hidden">
                <Card className="h-full flex flex-col">
                  <CardHeader className="flex-shrink-0">
                    <CardTitle className="flex items-center gap-2">
                      <CalendarDays className="h-5 w-5" /> Availability & Preferences
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-auto space-y-2 text-sm">
                    <div className="text-muted-foreground">Availability details not provided.</div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="scores" className="mt-4 flex-1 overflow-hidden">
                <div className="h-full overflow-auto">
                  <CandidateCompetencyCard candidate={candidate} />
                </div>
              </TabsContent>
            </Tabs>
          </div>

          {/* Right Column - Transcript (only on Scores tab) */}
          {activeTab === 'scores' && (
            <div className="col-span-1 lg:col-span-4 relative">
              <div className="absolute inset-1 overflow-hidden">
                <CandidateTranscriptCard candidate={candidate} />
              </div>
            </div>
          )}
        </div>
      </Main>
    </>
  )
}
