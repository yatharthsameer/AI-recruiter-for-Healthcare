import { createFileRoute } from '@tanstack/react-router'
import { CandidateDetailPage } from '@/features/candidates/components/candidate-detail-page'

export const Route = createFileRoute('/_authenticated/candidates/$candidateId')({
  component: CandidateDetailPage,
})
