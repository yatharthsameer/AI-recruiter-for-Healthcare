import z from 'zod'
import { createFileRoute } from '@tanstack/react-router'
import { Candidates } from '@/features/candidates'
import { recommendations, statuses } from '@/features/candidates/data/data'

const candidateSearchSchema = z.object({
  page: z.number().optional().catch(1),
  pageSize: z.number().optional().catch(10),
  status: z
    .array(z.enum(statuses.map((status) => status.value)))
    .optional()
    .catch([]),
  recommendation: z
    .array(z.enum(recommendations.map((rec) => rec.value)))
    .optional()
    .catch([]),
  filter: z.string().optional().catch(''),
  scoreRange: z.object({
    min: z.number().optional().catch(0),
    max: z.number().optional().catch(100),
  }).optional().catch({ min: 0, max: 100 }),
})

export const Route = createFileRoute('/_authenticated/candidates/')({
  validateSearch: candidateSearchSchema,
  component: Candidates,
})
