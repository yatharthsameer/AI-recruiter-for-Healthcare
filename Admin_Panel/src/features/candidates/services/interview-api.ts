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
      return this.transformInterviewData(data.interviews || [])
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
      // Transform to our Transcript schema including audio URLs and analysis
      return this.transformTranscriptData(data)
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
      const scores = evaluation.scores || {}
      
      // Map the evaluation scores to admin panel schema (using actual evaluation criteria)
      const competencyScores = {
        experience_skills: Math.min(10, Math.max(0, scores.experience_skills?.score || 0)),
        motivation: Math.min(10, Math.max(0, scores.motivation?.score || 0)),
        punctuality: Math.min(10, Math.max(0, scores.punctuality?.score || 0)),
        compassion_empathy: Math.min(10, Math.max(0, scores.compassion_empathy?.score || 0)),
        communication: Math.min(10, Math.max(0, scores.communication?.score || 0)),
      }
      
      // Calculate overall score from individual scores (already on 0-10 scale)
      const overallScore = scores.overall_score || 
        Math.round((competencyScores.experience_skills + competencyScores.motivation + 
                   competencyScores.punctuality + competencyScores.compassion_empathy + 
                   competencyScores.communication) / 5) // Keep on 0-10 scale
      
      return {
        id: interview.sessionId,
        candidateName: `${userData.firstName || ''} ${userData.lastName || ''}`.trim() || 'Unknown',
        email: userData.email || '',
        phone: userData.phone || '',
        position: 'caregiver', // Default position
        interviewType: interview.interviewType || 'caregiving',
        overallScore: Math.min(100, Math.max(0, Math.round(typeof overallScore === 'number' ? overallScore * 10 : 0))), // Convert 0-10 scale to 0-100 scale, clamped to 0-100
        recommendation: this.mapRecommendation(scores.recommendation),
        status: this.mapStatus(interview.status),
        interviewDate: interview.startTime || new Date().toISOString(),
        duration: interview.duration || 0,
        competencyScores,
        strengths: this.extractStrengths(scores),
        developmentAreas: this.extractDevelopmentAreas(scores),
        nextSteps: this.generateNextSteps(scores.recommendation),
        // Extract availability data from user_data
        driversLicense: userData.driversLicense || false,
        autoInsurance: userData.autoInsurance || false,
        availability: userData.availability || [],
        weeklyHours: userData.weeklyHours || 0,
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
    
    // Parse transcript entries from your actual format
    if (rawData.transcript && Array.isArray(rawData.transcript)) {
      let questionNumber = 0
      
      rawData.transcript.forEach((entry: any, index: number) => {
        const timestamp = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ''
        const rawTimestamp = entry.timestamp || ''
        
        if (entry.type === 'ai') {
          questionNumber++
          entries.push({
            type: 'question' as const,
            speaker: 'ai' as const,
            content: entry.message,
            timestamp,
            // preserve raw timestamp for precise seeking
            rawTimestamp,
            questionNumber,
          })
        } else if (entry.type === 'user') {
          entries.push({
            type: 'answer' as const,
            speaker: 'candidate' as const,
            content: entry.message,
            timestamp,
            rawTimestamp,
            questionNumber,
            duration: this.calculateResponseDurationFromIndex(rawData.transcript, index),
          })
        } else if (entry.type === 'system') {
          entries.push({
            type: 'system' as const,
            speaker: 'system' as const,
            content: entry.message,
            timestamp,
            rawTimestamp,
          })
        }
      })
    }
    
    // Generate audio segments from transcript timestamps
    const audioSegments = []
    if (rawData.transcript && Array.isArray(rawData.transcript)) {
      let questionNumber = 0
      
      rawData.transcript.forEach((entry: any, index: number) => {
        if (entry.type === 'user' && entry.timestamp) {
          // Find the corresponding question
          let questionStart = null
          for (let i = index - 1; i >= 0; i--) {
            if (rawData.transcript[i].type === 'ai') {
              questionStart = rawData.transcript[i].timestamp
              questionNumber++
              break
            }
          }
          
          if (questionStart && entry.timestamp) {
            try {
              const startTime = new Date(questionStart).getTime()
              const endTime = new Date(entry.timestamp).getTime() + 10000 // Add 10 seconds for response duration
              
              audioSegments.push({
                questionNumber,
                startMs: startTime - new Date(rawData.transcript[0].timestamp).getTime(),
                endMs: endTime - new Date(rawData.transcript[0].timestamp).getTime(),
              })
            } catch (error) {
              // Skip if timestamp parsing fails
            }
          }
        }
      })
    }

    const result: any = {
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

    // Pass through full audio if provided by backend, or create from audio metadata
    if (rawData.fullAudio?.url) {
      result.fullAudio = {
        url: `${API_BASE_URL}${rawData.fullAudio.url}`,
        segments: Array.isArray(rawData.fullAudio.segments) ? rawData.fullAudio.segments : audioSegments,
      }
    } else {
      // Create audio URL from metadata filename (backend now provides correct filename)
      const audioFilename = rawData.metadata?.audio_filename || `${rawData.sessionId}.webm`
      result.fullAudio = {
        url: `${API_BASE_URL}/interview-outputs/${audioFilename}`,
        segments: audioSegments,
      }
    }

    // Pass through competencySegments mapping to help UI jump precisely
    if (rawData.competencySegments && typeof rawData.competencySegments === 'object') {
      result.competencySegments = rawData.competencySegments
    }
    
    return result
  }

  /**
   * Map backend recommendation to frontend enum
   */
  private static mapRecommendation(recommendation: string): string {
    const mapping: Record<string, string> = {
      'highly_recommend': 'highly_recommended',
      'recommend': 'recommended', 
      'consider': 'consider_with_training',
      'not_recommend': 'not_recommended',
      // Legacy mappings
      'Highly Recommended': 'highly_recommended',
      'Recommended': 'recommended',
      'Consider with Training': 'consider_with_training',
      'Not Recommended': 'not_recommended',
    }
    
    return mapping[recommendation] || 'consider_with_training'
  }

  /**
   * Extract strengths from evaluation scores
   */
  private static extractStrengths(scores: any): string[] {
    const strengths: string[] = []
    
    if (scores.compassion_empathy?.score >= 8) {
      strengths.push('Strong empathy and compassion')
    }
    if (scores.communication?.score >= 8) {
      strengths.push('Excellent communication skills')
    }
    if (scores.experience_skills?.score >= 8) {
      strengths.push('Relevant caregiving experience')
    }
    if (scores.punctuality?.score >= 8) {
      strengths.push('Reliable and punctual')
    }
    if (scores.motivation?.score >= 8) {
      strengths.push('Strong motivation for caregiving')
    }
    
    // Add reasoning as strengths if available
    Object.values(scores).forEach((scoreObj: any) => {
      if (scoreObj?.reasoning && scoreObj?.score >= 8) {
        const reasoning = scoreObj.reasoning.toLowerCase()
        if (reasoning.includes('professional') && !strengths.some(s => s.includes('professional'))) {
          strengths.push('Professional demeanor')
        }
        if (reasoning.includes('patient') && !strengths.some(s => s.includes('patient'))) {
          strengths.push('Patient-centered approach')
        }
      }
    })
    
    return strengths.length > 0 ? strengths : ['Completed interview assessment']
  }

  /**
   * Extract development areas from evaluation scores
   */
  private static extractDevelopmentAreas(scores: any): string[] {
    const areas: string[] = []
    
    if (scores.compassion_empathy?.score < 7) {
      areas.push('Develop empathy and patient interaction skills')
    }
    if (scores.communication?.score < 7) {
      areas.push('Improve communication clarity')
    }
    if (scores.experience_skills?.score < 7) {
      areas.push('Gain more hands-on caregiving experience')
    }
    if (scores.punctuality?.score < 7) {
      areas.push('Improve punctuality and reliability')
    }
    if (scores.motivation?.score < 7) {
      areas.push('Strengthen commitment to caregiving career')
    }
    
    return areas.length > 0 ? areas : ['Continue professional development']
  }

  /**
   * Generate next steps based on recommendation
   */
  private static generateNextSteps(recommendation: string): string[] {
    const baseSteps = ['Reference checks', 'Background verification']
    
    switch (recommendation) {
      case 'highly_recommend':
        return [...baseSteps, 'Schedule orientation', 'Prepare job offer']
      case 'recommend':
        return [...baseSteps, 'Skills assessment', 'Final interview']
      case 'consider':
        return [...baseSteps, 'Additional training assessment', 'Follow-up interview']
      default:
        return [...baseSteps, 'Further evaluation needed']
    }
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
   * Calculate response duration from transcript array index
   */
  private static calculateResponseDurationFromIndex(transcript: any[], currentIndex: number): number {
    // Find the previous AI message (question)
    for (let i = currentIndex - 1; i >= 0; i--) {
      if (transcript[i].type === 'ai') {
        try {
          const questionTime = new Date(transcript[i].timestamp)
          const responseTime = new Date(transcript[currentIndex].timestamp)
          return Math.max(0, Math.floor((responseTime.getTime() - questionTime.getTime()) / 1000))
        } catch {
          return 0
        }
      }
    }
    return 0
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
