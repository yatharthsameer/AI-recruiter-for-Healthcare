import {
  CheckCircle,
  AlertCircle,
  Clock,
  XCircle,
  UserCheck,
  UserX,
  Timer,
  FileText,
} from 'lucide-react'

export const recommendations = [
  {
    value: 'highly_recommended',
    label: 'Highly Recommended',
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
  {
    value: 'recommended',
    label: 'Recommended',
    icon: UserCheck,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  {
    value: 'consider_with_training',
    label: 'Consider with Training',
    icon: AlertCircle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
  },
  {
    value: 'not_recommended',
    label: 'Not Recommended',
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
  },
]

export const statuses = [
  {
    label: 'Completed',
    value: 'completed' as const,
    icon: CheckCircle,
    color: 'text-green-600',
  },
  {
    label: 'Under Review',
    value: 'under_review' as const,
    icon: Clock,
    color: 'text-yellow-600',
  },
  {
    label: 'Hired',
    value: 'hired' as const,
    icon: UserCheck,
    color: 'text-green-600',
  },
  {
    label: 'Rejected',
    value: 'rejected' as const,
    icon: UserX,
    color: 'text-red-600',
  },
  {
    label: 'Follow-up Scheduled',
    value: 'follow_up' as const,
    icon: Timer,
    color: 'text-blue-600',
  },
]

export const positions = [
  {
    value: 'caregiver',
    label: 'Caregiver',
  },
  {
    value: 'home_health_aide',
    label: 'Home Health Aide',
  },
  {
    value: 'companion',
    label: 'Companion',
  },
  {
    value: 'nurse',
    label: 'Nurse',
  },
]

export const interviewTypes = [
  {
    value: 'general',
    label: 'General',
  },
  {
    value: 'home_care',
    label: 'Home Care',
  },
  {
    value: 'specialized',
    label: 'Specialized',
  },
]

// Score ranges for color coding
export const scoreRanges = {
  excellent: { min: 80, max: 100, color: 'text-green-600', bgColor: 'bg-green-50' },
  good: { min: 65, max: 79, color: 'text-blue-600', bgColor: 'bg-blue-50' },
  fair: { min: 50, max: 64, color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
  poor: { min: 0, max: 49, color: 'text-red-600', bgColor: 'bg-red-50' },
}

export const competencyLabels = {
  empathy_compassion: 'Empathy & Compassion',
  safety_awareness: 'Safety Awareness',
  communication_skills: 'Communication Skills',
  problem_solving: 'Problem Solving',
  experience_commitment: 'Experience & Commitment',
}
