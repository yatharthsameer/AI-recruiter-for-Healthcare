import { useState } from 'react'
import { X, Download, FileText, BarChart3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { type Candidate } from '../data/schema'
import { recommendations, statuses, competencyLabels, scoreRanges } from '../data/data'
import { CandidateProfilePanel } from './candidate-profile-panel'
import { TranscriptPanel } from './transcript/transcript-panel'
import { CompetencyChart } from './competency-chart'

interface CandidateDetailViewProps {
  candidate: Candidate
  onClose: () => void
}

export function CandidateDetailView({ candidate, onClose }: CandidateDetailViewProps) {
  const [activeTab, setActiveTab] = useState('profile')
  
  const recommendation = recommendations.find(r => r.value === candidate.recommendation)
  const status = statuses.find(s => s.value === candidate.status)
  const scoreColor = candidate.overallScore >= 80 ? scoreRanges.excellent : 
                    candidate.overallScore >= 65 ? scoreRanges.good :
                    candidate.overallScore >= 50 ? scoreRanges.fair : scoreRanges.poor

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
      <div className="fixed inset-4 z-50 grid gap-4 bg-background border rounded-lg shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-4">
            <div>
              <h2 className="text-2xl font-bold">{candidate.candidateName}</h2>
              <p className="text-muted-foreground">{candidate.email}</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${scoreColor.color} ${scoreColor.bgColor}`}>
                {candidate.overallScore}/100
              </div>
              {recommendation && (
                <Badge className={`${recommendation.color} ${recommendation.bgColor} ${recommendation.borderColor}`}>
                  <recommendation.icon className="mr-1 h-3 w-3" />
                  {recommendation.label}
                </Badge>
              )}
              {status && (
                <Badge variant="outline">
                  <status.icon className={`mr-1 h-3 w-3 ${status.color}`} />
                  {status.label}
                </Badge>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <div className="px-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="profile" className="flex items-center space-x-2">
                  <BarChart3 className="h-4 w-4" />
                  <span>Profile & Evaluation</span>
                </TabsTrigger>
                <TabsTrigger value="transcript" className="flex items-center space-x-2">
                  <FileText className="h-4 w-4" />
                  <span>Interview Transcript</span>
                </TabsTrigger>
                <TabsTrigger value="competencies" className="flex items-center space-x-2">
                  <BarChart3 className="h-4 w-4" />
                  <span>Competency Analysis</span>
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-hidden px-6 pb-6">
              <TabsContent value="profile" className="h-full mt-4">
                <CandidateProfilePanel candidate={candidate} />
              </TabsContent>

              <TabsContent value="transcript" className="h-full mt-4">
                <TranscriptPanel candidate={candidate} />
              </TabsContent>

              <TabsContent value="competencies" className="h-full mt-4">
                <div className="grid gap-6 h-full">
                  <Card>
                    <CardHeader>
                      <CardTitle>Competency Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CompetencyChart competencyScores={candidate.competencyScores} />
                    </CardContent>
                  </Card>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-green-600">Strengths</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {candidate.strengths.map((strength, index) => (
                            <li key={index} className="flex items-start space-x-2">
                              <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                              <span className="text-sm">{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-amber-600">Development Areas</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {candidate.developmentAreas.map((area, index) => (
                            <li key={index} className="flex items-start space-x-2">
                              <div className="w-2 h-2 bg-amber-500 rounded-full mt-2 flex-shrink-0" />
                              <span className="text-sm">{area}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
