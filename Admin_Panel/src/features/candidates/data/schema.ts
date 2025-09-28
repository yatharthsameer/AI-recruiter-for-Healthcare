import { z } from 'zod'

// Candidate schema for interview results
export const candidateSchema = z.object({
  id: z.string(), // sessionId
  candidateName: z.string(), // firstName + lastName
  email: z.string(),
  phone: z.string(),
  position: z.string(),
  interviewType: z.string(),
  overallScore: z.number().min(0).max(100),
  recommendation: z.string(), // "Highly Recommended", "Recommended", etc.
  status: z.string(), // "completed", "pending_review", "hired", "rejected"
  interviewDate: z.string(),
  duration: z.number(), // in seconds
  competencyScores: z.object({
    experience_skills: z.number().min(0).max(10),
    motivation: z.number().min(0).max(10),
    punctuality: z.number().min(0).max(10),
    compassion_empathy: z.number().min(0).max(10),
    communication: z.number().min(0).max(10),
  }),
  strengths: z.array(z.string()),
  developmentAreas: z.array(z.string()),
  nextSteps: z.array(z.string()),
  // Availability information from user_data
  driversLicense: z.boolean().optional(),
  autoInsurance: z.boolean().optional(),
  availability: z.array(z.string()).optional(), // ["Morning", "Afternoon", "Evening", "Overnight", "Weekend"]
  weeklyHours: z.number().optional(),
  // Additional fields for table display
  createdAt: z.date().optional(),
  updatedAt: z.date().optional(),
})

export type Candidate = z.infer<typeof candidateSchema>

// Transcript schema for detailed interview review
export const transcriptEntrySchema = z.object({
  type: z.enum(['question', 'answer', 'system']),
  speaker: z.enum(['ai', 'candidate', 'system']),
  content: z.string(),
  timestamp: z.string(),
  duration: z.number().optional(), // for answers
  questionNumber: z.number().optional(),
  analysis: z.object({
    sentiment: z.string(),
    keyTerms: z.array(z.string()),
    scoreImpact: z.record(z.number()),
    flags: z.array(z.string()).optional(), // concerns, positives
  }).optional(),
})

export const transcriptSchema = z.object({
  sessionId: z.string(),
  entries: z.array(transcriptEntrySchema),
  metadata: z.object({
    totalDuration: z.number(),
    audioQuality: z.number(),
    interruptions: z.number(),
    connectionIssues: z.array(z.string()),
    clientInfo: z.object({
      ip: z.string(),
      userAgent: z.string(),
      location: z.string().optional(),
    }),
  }),
})

export type TranscriptEntry = z.infer<typeof transcriptEntrySchema>
export type Transcript = z.infer<typeof transcriptSchema>