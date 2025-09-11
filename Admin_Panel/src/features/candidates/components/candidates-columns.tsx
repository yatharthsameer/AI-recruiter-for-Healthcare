import { type ColumnDef } from '@tanstack/react-table'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { DataTableColumnHeader } from '@/components/data-table'
import { recommendations, statuses, positions, scoreRanges } from '../data/data'
import { type Candidate } from '../data/schema'
import { DataTableRowActions } from './data-table-row-actions'
import { ClickableCandidateCell } from './clickable-candidate-cell'
import { format } from 'date-fns'

// Helper function to get score color
const getScoreColor = (score: number) => {
  if (score >= 80) return scoreRanges.excellent
  if (score >= 65) return scoreRanges.good
  if (score >= 50) return scoreRanges.fair
  return scoreRanges.poor
}

// Helper function to format duration
const formatDuration = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

export const candidatesColumns: ColumnDef<Candidate>[] = [
  {
    id: 'select',
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && 'indeterminate')
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label='Select all'
        className='translate-y-[2px]'
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label='Select row'
        className='translate-y-[2px]'
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: 'candidateName',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Candidate' />
    ),
    cell: ({ row }) => {
      return <ClickableCandidateCell candidate={row.original} />
    },
    enableSorting: true,
    enableHiding: false,
  },
  {
    accessorKey: 'overallScore',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Score' />
    ),
    cell: ({ row }) => {
      const score = row.getValue('overallScore') as number
      const scoreColor = getScoreColor(score)
      
      return (
        <div className='flex items-center space-x-2'>
          <div 
            className={`px-2 py-1 rounded-md text-sm font-medium ${scoreColor.color} ${scoreColor.bgColor}`}
          >
            {score}/100
          </div>
        </div>
      )
    },
    enableSorting: true,
    sortingFn: 'basic',
  },
  {
    accessorKey: 'recommendation',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Recommendation' />
    ),
    cell: ({ row }) => {
      const recommendation = recommendations.find(
        (rec) => rec.value === row.getValue('recommendation')
      )

      if (!recommendation) {
        return null
      }

      return (
        <div className='flex items-center space-x-2'>
          <Badge 
            variant='outline' 
            className={`${recommendation.color} ${recommendation.bgColor} ${recommendation.borderColor}`}
          >
            <recommendation.icon className='mr-1 size-3' />
            {recommendation.label}
          </Badge>
        </div>
      )
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id))
    },
  },
  {
    accessorKey: 'status',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Status' />
    ),
    cell: ({ row }) => {
      const status = statuses.find(
        (status) => status.value === row.getValue('status')
      )

      if (!status) {
        return null
      }

      return (
        <div className='flex items-center space-x-2'>
          <status.icon className={`size-4 ${status.color}`} />
          <span className='text-sm'>{status.label}</span>
        </div>
      )
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id))
    },
  },
  {
    accessorKey: 'interviewDate',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Interview Date' />
    ),
    cell: ({ row }) => {
      const date = new Date(row.getValue('interviewDate'))
      return (
        <div className='flex flex-col space-y-1'>
          <div className='text-sm'>{format(date, 'MMM dd, yyyy')}</div>
          <div className='text-xs text-muted-foreground'>
            {formatDuration(row.original.duration)}
          </div>
        </div>
      )
    },
    enableSorting: true,
    sortingFn: 'datetime',
  },
  {
    id: 'competencies',
    header: 'Key Competencies',
    cell: ({ row }) => {
      const competencies = row.original.competencyScores
      const topCompetencies = Object.entries(competencies)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 2)
        .map(([key, value]) => ({
          name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          score: value
        }))
      
      return (
        <div className='flex flex-col space-y-1'>
          {topCompetencies.map((comp, index) => (
            <div key={index} className='flex items-center space-x-2'>
              <div className='text-xs text-muted-foreground'>{comp.name}:</div>
              <div className={`text-xs font-medium ${getScoreColor(comp.score * 10).color}`}>
                {comp.score}/10
              </div>
            </div>
          ))}
        </div>
      )
    },
    enableSorting: false,
  },
  {
    id: 'actions',
    cell: ({ row }) => <DataTableRowActions row={row} />,
  },
]
