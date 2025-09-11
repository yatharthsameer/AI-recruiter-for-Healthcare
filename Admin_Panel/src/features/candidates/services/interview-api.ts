import { type Candidate, type Transcript } from '../data/schema'

// API configuration
const API_BASE_URL = 'http://localhost:8000' // Python backend URL
const INTERVIEW_OUTPUTS_PATH = '/api/interviews'

export class InterviewApiService {
  /**
   * Fetch all completed interviews
   */
  static async fetchInterviews(): Promise<Candidate[]> {
    try {
      const response = await fetch(`${API_BASE_URL}${INTERVIEW_OUTPUTS_PATH}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch interviews: ${response.statusText}`)
      }
      
      const data = await response.json()
      return this.transformInterviewData(data)
    } catch (error) {
      console.error('Error fetching interviews:', error)
      // Return empty array on error - in production, you might want to show an error state
      return []
    }
  }

  /**
   * Fetch specific interview transcript
   */
  static async fetchTranscript(sessionId: string): Promise<Transcript | null> {
    try {
      const response = await fetch(`${API_BASE_URL}${INTERVIEW_OUTPUTS_PATH}/${sessionId}/transcript`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch transcript: ${response.statusText}`)
      }
      
      const data = await response.json()
      // Return the raw data since it's already in the correct format
      return data
    } catch (error) {
      console.error('Error fetching transcript:', error)
      return null
    }
  }

  /**
   * Fetch interview evaluation report
   */
  static async fetchEvaluation(sessionId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}${INTERVIEW_OUTPUTS_PATH}/${sessionId}/evaluation`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch evaluation: ${response.statusText}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching evaluation:', error)
      return null
    }
  }

  /**
   * Transform raw interview data from backend to Candidate schema
   */
  private static transformInterviewData(rawData: any[]): Candidate[] {
    return rawData.map(interview => {
      const userData = interview.userData || {}
      const evaluation = interview.caregiverEvaluation || {}
      
      return {
        id: interview.sessionId,
        candidateName: `${userData.firstName || ''} ${userData.lastName || ''}`.trim() || 'Unknown',
        email: userData.email || '',
        phone: userData.phone || '',
        position: userData.position || 'caregiver',
        interviewType: interview.interviewType || 'general',
        overallScore: evaluation.overallScore || 0,
        recommendation: this.mapRecommendation(evaluation.recommendation?.recommendation),
        status: this.mapStatus(interview.status),
        interviewDate: interview.startTime || new Date().toISOString(),
        duration: interview.duration || 0,
        competencyScores: {
          empathy_compassion: evaluation.competencyScores?.empathy_compassion || 0,
          safety_awareness: evaluation.competencyScores?.safety_awareness || 0,
          communication_skills: evaluation.competencyScores?.communication_skills || 0,
          problem_solving: evaluation.competencyScores?.problem_solving || 0,
          experience_commitment: evaluation.competencyScores?.experience_commitment || 0,
        },
        strengths: evaluation.strengths || [],
        developmentAreas: evaluation.developmentAreas || [],
        nextSteps: evaluation.nextSteps || [],
        createdAt: new Date(interview.startTime || Date.now()),
        updatedAt: new Date(interview.endTime || Date.now()),
      }
    })
  }

  /**
   * Transform raw transcript data to Transcript schema
   */
  private static transformTranscriptData(rawData: any): Transcript {
    const entries = []
    
    // Parse questions and responses from transcript
    if (rawData.questions && rawData.responses) {
      for (let i = 0; i < rawData.questions.length; i++) {
        const question = rawData.questions[i]
        const response = rawData.responses[i]
        
        // Add question entry
        entries.push({
          type: 'question' as const,
          speaker: 'ai' as const,
          content: question.question,
          timestamp: new Date(question.timestamp).toLocaleTimeString(),
          questionNumber: question.questionNumber,
        })
        
        // Add response entry if exists
        if (response) {
          entries.push({
            type: 'answer' as const,
            speaker: 'candidate' as const,
            content: response.response,
            timestamp: new Date(response.timestamp).toLocaleTimeString(),
            duration: this.calculateResponseDuration(question.timestamp, response.timestamp),
            questionNumber: response.questionNumber,
            analysis: response.analysis ? {
              sentiment: this.analyzeSentiment(response.response),
              keyTerms: this.extractKeyTerms(response.response),
              scoreImpact: response.analysis.scoreImpact || {},
              flags: response.analysis.flags || [],
            } : undefined,
          })
        }
      }
    }
    
    return {
      sessionId: rawData.sessionId,
      entries,
      metadata: {
        totalDuration: rawData.duration || 0,
        audioQuality: 8, // Default value - would come from actual audio analysis
        interruptions: 0, // Would be calculated from audio analysis
        connectionIssues: [],
        clientInfo: {
          ip: rawData.metadata?.clientIp || 'Unknown',
          userAgent: rawData.metadata?.userAgent || 'Unknown',
          location: rawData.metadata?.location,
        },
      },
    }
  }

  /**
   * Map backend recommendation to frontend enum
   */
  private static mapRecommendation(recommendation: string): string {
    const mapping: Record<string, string> = {
      'Highly Recommended': 'highly_recommended',
      'Recommended': 'recommended',
      'Consider with Training': 'consider_with_training',
      'Not Recommended': 'not_recommended',
    }
    
    return mapping[recommendation] || 'consider_with_training'
  }

  /**
   * Map backend status to frontend enum
   */
  private static mapStatus(status: string): string {
    const mapping: Record<string, string> = {
      'completed': 'completed',
      'active': 'under_review',
      'pending': 'under_review',
      'error': 'under_review',
    }
    
    return mapping[status] || 'completed'
  }

  /**
   * Calculate response duration between question and answer timestamps
   */
  private static calculateResponseDuration(questionTime: string, responseTime: string): number {
    const questionDate = new Date(questionTime)
    const responseDate = new Date(responseTime)
    return Math.max(0, Math.floor((responseDate.getTime() - questionDate.getTime()) / 1000))
  }

  /**
   * Analyze sentiment of response text
   */
  private static analyzeSentiment(text: string): string {
    const lowerText = text.toLowerCase()
    
    // Simple sentiment analysis - in production, you'd use a proper NLP service
    const positiveWords = ['good', 'great', 'excellent', 'happy', 'love', 'enjoy', 'wonderful']
    const negativeWords = ['bad', 'terrible', 'hate', 'awful', 'horrible', 'difficult', 'problem']
    const concerningWords = ['unsafe', 'dangerous', 'illegal', 'wrong', 'hide', 'secret']
    
    if (concerningWords.some(word => lowerText.includes(word))) return 'concerning'
    if (positiveWords.some(word => lowerText.includes(word))) return 'positive'
    if (negativeWords.some(word => lowerText.includes(word))) return 'negative'
    
    return 'neutral'
  }

  /**
   * Extract key terms from response text
   */
  private static extractKeyTerms(text: string): string[] {
    const words = text.toLowerCase().split(/\W+/)
    const stopWords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'uh', 'um', 'so', 'well', 'like', 'just', 'really', 'very', 'actually', 'basically'])
    
    const relevantWords = words
      .filter(word => word.length > 3 && !stopWords.has(word))
      .filter(word => /^[a-z]+$/.test(word)) // Only alphabetic words
    
    // Count word frequency and return top terms
    const wordCount: Record<string, number> = {}
    relevantWords.forEach(word => {
      wordCount[word] = (wordCount[word] || 0) + 1
    })
    
    return Object.entries(wordCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([word]) => word)
  }
}

// Hook for using interview data in React components
export function useInterviews() {
  // This would typically use React Query or SWR for caching and state management
  // For now, we'll return a simple promise-based approach
  
  return {
    fetchInterviews: InterviewApiService.fetchInterviews,
    fetchTranscript: InterviewApiService.fetchTranscript,
    fetchEvaluation: InterviewApiService.fetchEvaluation,
  }
}
