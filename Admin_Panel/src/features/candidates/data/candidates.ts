import { faker } from '@faker-js/faker'
import { type Candidate } from './schema'
import { InterviewApiService } from '../services/interview-api'

// Set a fixed seed for consistent data generation
faker.seed(12345)

// Function to load real interview data
export async function loadCandidatesFromApi(): Promise<Candidate[]> {
  try {
    const realData = await InterviewApiService.fetchInterviews()
    if (realData.length > 0) {
      return realData // Only return real data, no sample data
    }
  } catch (error) {
    console.warn('Failed to load real interview data, using sample data:', error)
  }
  
  // Only use sample data as fallback if API fails
  return generateSampleCandidates(5) // Reduced sample size for fallback
}

function generateSampleCandidates(count: number): Candidate[] {
  return Array.from({ length: count }, () => {
    const firstName = faker.person.firstName()
    const lastName = faker.person.lastName()
    const score = faker.number.int({ min: 25, max: 95 })
    
    let recommendation: string
    if (score >= 80) recommendation = 'highly_recommended'
    else if (score >= 65) recommendation = 'recommended'
    else if (score >= 50) recommendation = 'consider_with_training'
    else recommendation = 'not_recommended'

    const statuses = ['completed', 'under_review', 'hired', 'rejected', 'follow_up']
    const positions = ['caregiver', 'home_health_aide', 'companion', 'nurse']
    const interviewTypes = ['general', 'home_care', 'specialized']

    return {
      id: faker.string.uuid(),
      candidateName: `${firstName} ${lastName}`,
      email: faker.internet.email({ firstName, lastName }),
      phone: faker.phone.number(),
      position: faker.helpers.arrayElement(positions),
      interviewType: faker.helpers.arrayElement(interviewTypes),
      overallScore: score,
      recommendation,
      status: faker.helpers.arrayElement(statuses),
      interviewDate: faker.date.past({ years: 0.5 }).toISOString(),
      duration: faker.number.int({ min: 120, max: 600 }),
      competencyScores: {
        empathy_compassion: faker.number.int({ min: 3, max: 10 }),
        safety_awareness: faker.number.int({ min: 3, max: 10 }),
        communication_skills: faker.number.int({ min: 3, max: 10 }),
        problem_solving: faker.number.int({ min: 3, max: 10 }),
        experience_commitment: faker.number.int({ min: 3, max: 10 }),
      },
      strengths: Array.from({ length: faker.number.int({ min: 2, max: 5 }) }, () =>
        faker.helpers.arrayElement([
          'Strong Communication Skills',
          'Relevant Experience',
          'CPR Certified',
          'Reliable Transportation',
          'Flexible Schedule',
          'Empathetic Approach',
          'Problem-Solving Abilities',
          'Professional Demeanor',
          'Safety Conscious',
          'Team Player',
        ])
      ),
      developmentAreas: Array.from({ length: faker.number.int({ min: 1, max: 4 }) }, () =>
        faker.helpers.arrayElement([
          'Needs additional training',
          'Improve communication clarity',
          'Develop problem-solving skills',
          'Gain more experience',
          'Enhance safety awareness',
          'Build confidence',
          'Learn new techniques',
          'Improve time management',
        ])
      ),
      nextSteps: Array.from({ length: faker.number.int({ min: 2, max: 4 }) }, () =>
        faker.helpers.arrayElement([
          'Reference checks',
          'Background verification',
          'Skills assessment',
          'Training program',
          'Follow-up interview',
          'Orientation scheduling',
          'Documentation review',
          'Final approval',
        ])
      ),
      createdAt: faker.date.past({ years: 0.5 }),
      updatedAt: faker.date.recent(),
    }
  })
}

// Default export for backward compatibility (will be replaced by API data)
export const candidates = generateSampleCandidates(25)
