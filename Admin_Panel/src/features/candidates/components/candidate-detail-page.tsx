import { useState } from 'react'
import { useParams, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Download, UserCheck, UserX, RefreshCw, FileText, CalendarDays, ChevronDown, ChevronRight, Eye, CheckCircle, AlertCircle, Circle, MoreVertical, Phone, Mail, MessageSquare, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { useCandidatesData } from '../hooks/use-candidates-data'
import { recommendations, statuses, scoreRanges } from '../data/data'
import { CandidateCompetencyCard } from './cards/candidate-competency-card'
import { CandidateNextStepsCard } from './cards/candidate-next-steps-card'
import { CandidateTranscriptCard } from './cards/candidate-transcript-card'
import { CandidateExperienceSkillsCard } from './cards/candidate-experience-skills-card'

export function CandidateDetailPage() {
  const { candidateId } = useParams({ from: '/_authenticated/candidates/$candidateId' })
  const navigate = useNavigate()
  const { candidates, loading, error } = useCandidatesData()
  
  const candidate = candidates.find(c => c.id === candidateId)
  const [activeTab, setActiveTab] = useState('candidate_info')
  const [expandedDocs, setExpandedDocs] = useState<Set<string>>(new Set())

  type DocumentItem = {
    key: string
    label: string
    expiry?: string | null
    details?: {
      issuer?: string
      documentNumber?: string
      issueDate?: string
      verificationStatus?: string
      notes?: string
    }
  }

  // Enhanced document data with extracted information
  const documentItems: DocumentItem[] = [
    { 
      key: 'driving_license', 
      label: 'Driver\'s License', 
      expiry: '2026-03-15',
      details: {
        issuer: 'California DMV',
        documentNumber: 'D1234567',
        issueDate: '2022-03-15',
        verificationStatus: 'Verified',
        notes: 'Class C license, no restrictions'
      }
    },
    { 
      key: 'auto_insurance', 
      label: 'Auto Insurance', 
      expiry: '2024-07-31',
      details: {
        issuer: 'State Farm Insurance',
        documentNumber: 'SF-789456123',
        issueDate: '2023-08-01',
        verificationStatus: 'Expired - Renewal Required',
        notes: 'Liability coverage $100k/$300k'
      }
    },
    { 
      key: 'i9_form', 
      label: 'I-9 Employment Form', 
      expiry: null,
      details: {
        issuer: 'HR Department',
        documentNumber: 'I9-2024-001',
        issueDate: '2024-01-15',
        verificationStatus: 'Complete',
        notes: 'US Citizen verification completed'
      }
    },
    { 
      key: 'tb_test', 
      label: 'TB Test Results', 
      expiry: '2024-05-10',
      details: {
        issuer: 'LabCorp',
        documentNumber: 'TB-456789',
        issueDate: '2023-05-10',
        verificationStatus: 'Expired - Retest Required',
        notes: 'Negative result, annual renewal required'
      }
    },
    { 
      key: 'cpr_certification', 
      label: 'CPR Certification', 
      expiry: '2025-12-20',
      details: {
        issuer: 'American Red Cross',
        documentNumber: 'CPR-2023-789',
        issueDate: '2023-12-20',
        verificationStatus: 'Valid',
        notes: 'Adult/Child CPR + AED certified'
      }
    },
    { 
      key: 'background_check', 
      label: 'Background Check', 
      expiry: '2025-09-15',
      details: {
        issuer: 'Sterling Volunteers',
        documentNumber: 'BG-2024-456',
        issueDate: '2024-09-15',
        verificationStatus: 'Clear',
        notes: 'Federal and state criminal history check'
      }
    },
    { 
      key: 'drug_screening', 
      label: 'Drug Screening', 
      expiry: '2024-11-30',
      details: {
        issuer: 'Quest Diagnostics',
        documentNumber: 'DS-2023-321',
        issueDate: '2023-11-30',
        verificationStatus: 'Expired - Retest Required',
        notes: '10-panel drug screen, negative results'
      }
    },
    { 
      key: 'hha_certification', 
      label: 'HHA Certification', 
      expiry: '2026-01-10',
      details: {
        issuer: 'State Health Department',
        documentNumber: 'HHA-2024-123',
        issueDate: '2024-01-10',
        verificationStatus: 'Active',
        notes: '75-hour training program completed'
      }
    },
  ]

  const getDocStatus = (expiry?: string | null) => {
    if (!expiry) return { 
      text: 'No Expiry', 
      badgeVariant: 'secondary' as const, 
      badgeClass: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200', 
      extra: 'Permanent document' 
    }
    const exp = new Date(expiry)
    const now = new Date()
    if (isNaN(exp.getTime())) return { 
      text: 'Unknown', 
      badgeVariant: 'secondary' as const, 
      badgeClass: 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200', 
      extra: '' 
    }
    const expired = exp < now
    const daysUntilExpiry = Math.ceil((exp.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    
    if (expired) {
      return { 
        text: 'Expired', 
        badgeVariant: 'destructive' as const, 
        badgeClass: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200', 
        extra: `${Math.abs(daysUntilExpiry)} days ago` 
      }
    } else if (daysUntilExpiry <= 30) {
      return { 
        text: 'Expiring Soon', 
        badgeVariant: 'outline' as const, 
        badgeClass: 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-200', 
        extra: `${daysUntilExpiry} days left` 
      }
    } else {
      return { 
        text: 'Valid', 
        badgeVariant: 'outline' as const, 
        badgeClass: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200', 
        extra: `${daysUntilExpiry} days left` 
      }
    }
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

  const toggleDocExpansion = (docKey: string) => {
    const newExpanded = new Set(expandedDocs)
    if (newExpanded.has(docKey)) {
      newExpanded.delete(docKey)
    } else {
      newExpanded.add(docKey)
    }
    setExpandedDocs(newExpanded)
  }

  const handleDocumentDownload = (doc: DocumentItem) => {
    // Placeholder for actual download functionality
    console.log(`Downloading ${doc.label}...`)
    // In real implementation, this would trigger a download from the backend
  }

  // Progress stages configuration
  const progressStages = [
    { key: 'applied', label: 'Applied', icon: CheckCircle },
    { key: 'interviewed', label: 'Interviewed', icon: CheckCircle },
    { key: 'background_check', label: 'Background Check', icon: Clock },
    { key: 'references', label: 'References', icon: AlertCircle },
    { key: 'onboarding', label: 'Onboarding', icon: Circle },
  ]

  // Determine current stage based on candidate status and next steps
  const getCurrentStageIndex = () => {
    // This logic can be enhanced based on actual candidate data
    if (candidate.status === 'completed') return 2 // Background check in progress
    if (candidate.status === 'under_review') return 1 // Interview completed
    return 0 // Just applied
  }

  const currentStageIndex = getCurrentStageIndex()

  const getStageStatus = (index: number) => {
    if (index < currentStageIndex) return 'completed'
    if (index === currentStageIndex) return 'in_progress'
    if (index === currentStageIndex + 1) return 'pending'
    return 'not_started'
  }

  const getStageStyles = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          badge: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200',
          icon: 'text-green-600',
        }
      case 'in_progress':
        return {
          badge: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200',
          icon: 'text-blue-600 animate-pulse',
        }
      case 'pending':
        return {
          badge: 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-200',
          icon: 'text-orange-600',
        }
      default:
        return {
          badge: 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200',
          icon: 'text-gray-400',
        }
    }
  }

  // Helper functions for enhanced top bar
  const getUrgentAlerts = () => {
    const alerts = []
    let expiredCount = 0
    
    documentItems.forEach(doc => {
      if (doc.expiry) {
        const exp = new Date(doc.expiry)
        const now = new Date()
        if (exp < now) {
          expiredCount++
        }
      }
    })
    
    if (expiredCount > 0) {
      alerts.push(`${expiredCount} doc${expiredCount > 1 ? 's' : ''} expired`)
    }
    
    return alerts
  }

  const getPrimaryAction = () => {
    const stage = progressStages[currentStageIndex]
    switch (stage?.key) {
      case 'applied':
        return { label: 'Schedule Interview', variant: 'default' as const, icon: Clock }
      case 'interviewed':
        return { label: 'Start Background Check', variant: 'default' as const, icon: CheckCircle }
      case 'background_check':
        return { label: 'Contact References', variant: 'default' as const, icon: Phone }
      case 'references':
        return { label: 'Begin Onboarding', variant: 'default' as const, icon: UserCheck }
      default:
        return { label: 'Hire Candidate', variant: 'default' as const, icon: UserCheck }
    }
  }

  const urgentAlerts = getUrgentAlerts()
  const primaryAction = getPrimaryAction()

  const getStatusLine = () => {
    const current = progressStages[currentStageIndex]?.label
    const next = progressStages[currentStageIndex + 1]?.label
    const alerts = getUrgentAlerts()
    
    let statusText = `${current}`
    if (next) statusText += ` → ${next}`
    if (alerts.length > 0) statusText += ` • ⚠️ ${alerts[0]}`
    
    return statusText
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

        {/* Clean Two-Row Top Bar */}
        <Card className="mb-6">
          <CardHeader>
            <div className="space-y-3">
              {/* Row 1: Identity & Actions */}
              <div className="flex items-center justify-between">
                {/* Left: Candidate Identity */}
                <div className="flex items-center space-x-4">
                  <Avatar className="h-12 w-12">
                    <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${candidate.candidateName}`} />
                    <AvatarFallback className="text-lg">
                      {getInitials(candidate.candidateName)}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div className="flex items-center space-x-2">
                    <CardTitle className="text-xl">{candidate.candidateName}</CardTitle>
                    <Badge className={`${scoreColor.bgColor} ${scoreColor.color} ${scoreColor.borderColor} text-sm font-bold px-2 py-1`}>
                      {candidate.overallScore}
                    </Badge>
                    <span className="text-muted-foreground">-</span>
                    <span className="text-sm font-medium capitalize">{candidate.position}</span>
                  </div>
                </div>

                {/* Right: Primary Actions */}
                <div className="flex items-center space-x-2">
                  <Button variant={primaryAction.variant} size="sm">
                    <primaryAction.icon className="mr-2 h-4 w-4" />
                    {primaryAction.label}
                  </Button>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Mail className="mr-2 h-4 w-4" />
                        Send Email
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Phone className="mr-2 h-4 w-4" />
                        Call Candidate
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <MessageSquare className="mr-2 h-4 w-4" />
                        Add Note
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Download className="mr-2 h-4 w-4" />
                        Export Report
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-green-600">
                        <UserCheck className="mr-2 h-4 w-4" />
                        Hire Candidate
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-red-600">
                        <UserX className="mr-2 h-4 w-4" />
                        Reject Candidate
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>

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

              {/* Row 2: Contact & Status */}
              <div className="flex items-center justify-between">
                {/* Left: Contact Information */}
                <div className="flex items-center space-x-4 text-sm text-muted-foreground ml-16">
                  <span>{candidate.email}</span>
                  <span>•</span>
                  <span>{candidate.phone}</span>
                </div>

                {/* Center: Single Status Line */}
                <div className="text-sm text-foreground">
                  {getStatusLine()}
                </div>

                {/* Right: Empty for alignment */}
                <div></div>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Main Tabs for Section Toggle */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="candidate_info">Candidate Information</TabsTrigger>
            <TabsTrigger value="interview_results">Interview Results</TabsTrigger>
          </TabsList>

          {/* Section 1: Candidate Information */}
          <TabsContent value="candidate_info" className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-xl">Candidate Information</CardTitle>
                    <p className="text-muted-foreground">Personal details, experience, documents, and availability</p>
                  </div>
                  
                  {/* Progress Bubbles */}
                  <div className="flex flex-col items-end space-y-2">
                    <div className="flex items-center space-x-1">
                      {progressStages.map((stage, index) => {
                        const status = getStageStatus(index)
                        const styles = getStageStyles(status)
                        const IconComponent = stage.icon
                        
                        return (
                          <div key={stage.key} className="flex items-center">
                            <div 
                              className={`flex items-center space-x-1 px-2 py-1 rounded-full border text-xs font-medium ${styles.badge}`}
                              title={`${stage.label} - ${status.replace('_', ' ')}`}
                            >
                              <IconComponent className={`h-3 w-3 ${styles.icon}`} />
                              <span className="hidden sm:inline">{stage.label}</span>
                            </div>
                            {index < progressStages.length - 1 && (
                              <div className="w-2 h-px bg-muted-foreground/30 mx-1" />
                            )}
                          </div>
                        )
                      })}
                    </div>
                    
                    {/* Current Status */}
                    <div className="text-xs text-muted-foreground text-right">
                      <span className="font-medium">Current:</span> {progressStages[currentStageIndex]?.label}
                      {currentStageIndex < progressStages.length - 1 && (
                        <>
                          <span className="mx-1">→</span>
                          <span className="font-medium">Next:</span> {progressStages[currentStageIndex + 1]?.label}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* 2 Column Layout - Pure Candidate Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Column: Experience & Skills + Availability */}
                  <div className="h-full">
                    <CandidateExperienceSkillsCard candidate={candidate} />
                  </div>

                  {/* Right Column: Documents Only */}
                  <div className="h-full">
                    <Card className="h-full">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <FileText className="h-5 w-5" /> Documents
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {documentItems.map((doc) => {
                          const status = getDocStatus(doc.expiry)
                          const isExpanded = expandedDocs.has(doc.key)
                          return (
                            <div key={doc.key} className="border rounded-lg">
                              {/* Main Document Row */}
                              <div className="flex items-center justify-between p-3 hover:bg-muted/50 transition-colors">
                                <div className="flex items-center gap-3 flex-1">
                                  <button
                                    onClick={() => toggleDocExpansion(doc.key)}
                                    className="flex items-center justify-center w-6 h-6 rounded hover:bg-muted transition-colors"
                                  >
                                    {isExpanded ? (
                                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                    )}
                                  </button>
                                  <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                  <span className="text-sm font-medium flex-1">{doc.label}</span>
                                </div>
                                
                                <div className="flex items-center gap-2">
                                  <Badge variant={status.badgeVariant} className={`text-xs ${status.badgeClass}`}>
                                    {status.text}
                                  </Badge>
                                  {status.extra && (
                                    <span className="text-xs text-muted-foreground hidden sm:inline">
                                      {status.extra}
                                    </span>
                                  )}
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDocumentDownload(doc)}
                                    className="h-8 w-8 p-0"
                                    title="Download document"
                                  >
                                    <Download className="h-4 w-4" />
                                  </Button>
                                </div>
                              </div>

                              {/* Expanded Details */}
                              {isExpanded && doc.details && (
                                <div className="px-3 pb-3 border-t bg-muted/20">
                                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 text-xs">
                                    {doc.details.issuer && (
                                      <div>
                                        <span className="font-medium text-muted-foreground">Issuer:</span>
                                        <div className="mt-1">{doc.details.issuer}</div>
                                      </div>
                                    )}
                                    {doc.details.documentNumber && (
                                      <div>
                                        <span className="font-medium text-muted-foreground">Document #:</span>
                                        <div className="mt-1 font-mono">{doc.details.documentNumber}</div>
                                      </div>
                                    )}
                                    {doc.details.issueDate && (
                                      <div>
                                        <span className="font-medium text-muted-foreground">Issue Date:</span>
                                        <div className="mt-1">{new Date(doc.details.issueDate).toLocaleDateString()}</div>
                                      </div>
                                    )}
                                    {doc.details.verificationStatus && (
                                      <div>
                                        <span className="font-medium text-muted-foreground">Status:</span>
                                        <div className="mt-1">{doc.details.verificationStatus}</div>
                                      </div>
                                    )}
                                  </div>
                                  {doc.details.notes && (
                                    <div className="mt-3 pt-2 border-t">
                                      <span className="font-medium text-muted-foreground text-xs">Notes:</span>
                                      <div className="mt-1 text-xs text-muted-foreground">{doc.details.notes}</div>
                                    </div>
                                  )}
                                  <div className="mt-3 flex gap-2">
                                    <Button variant="outline" size="sm" className="h-7 text-xs">
                                      <Eye className="h-3 w-3 mr-1" />
                                      View
                                    </Button>
                                    <Button variant="outline" size="sm" className="h-7 text-xs">
                                      <Download className="h-3 w-3 mr-1" />
                                      Download
                                    </Button>
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                        <p className="text-xs text-muted-foreground mt-4">Document verification status updated automatically.</p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Section 2: Interview Results */}
          <TabsContent value="interview_results" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Interview Results</CardTitle>
                <p className="text-muted-foreground">Competency scores, transcript, and evaluation details</p>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-7 gap-6 h-[700px]">
                  <div className="col-span-1 lg:col-span-3 flex">
                    <CandidateCompetencyCard candidate={candidate} />
                  </div>
                  <div className="col-span-1 lg:col-span-4 flex">
                    <CandidateTranscriptCard candidate={candidate} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}

