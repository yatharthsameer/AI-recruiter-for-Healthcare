import { DotsHorizontalIcon } from '@radix-ui/react-icons'
import { type Row } from '@tanstack/react-table'
import { Eye, FileText, Download, UserCheck, UserX } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { statuses } from '../data/data'
import { candidateSchema } from '../data/schema'

type DataTableRowActionsProps<TData> = {
  row: Row<TData>
}

export function DataTableRowActions<TData>({
  row,
}: DataTableRowActionsProps<TData>) {
  const candidate = candidateSchema.parse(row.original)
  const navigate = useNavigate()

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button
          variant='ghost'
          className='data-[state=open]:bg-muted flex h-8 w-8 p-0'
        >
          <DotsHorizontalIcon className='h-4 w-4' />
          <span className='sr-only'>Open menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align='end' className='w-[180px]'>
        <DropdownMenuItem
          onClick={() => {
            navigate({ to: '/candidates/$candidateId', params: { candidateId: candidate.id } })
          }}
        >
          <Eye className='mr-2 h-4 w-4' />
          View Details
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => {
            navigate({ to: '/candidates/$candidateId', params: { candidateId: candidate.id } })
          }}
        >
          <FileText className='mr-2 h-4 w-4' />
          View Transcript
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => {
            // TODO: Implement export functionality
            console.log('Export report for', candidate.candidateName)
          }}
        >
          <Download className='mr-2 h-4 w-4' />
          Export Report
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>Update Status</DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuRadioGroup value={candidate.status}>
              {statuses.map((status) => (
                <DropdownMenuRadioItem key={status.value} value={status.value}>
                  <status.icon className='mr-2 h-4 w-4' />
                  {status.label}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuSubContent>
        </DropdownMenuSub>
        <DropdownMenuSeparator />
        <DropdownMenuItem className='text-green-600'>
          <UserCheck className='mr-2 h-4 w-4' />
          Hire Candidate
        </DropdownMenuItem>
        <DropdownMenuItem className='text-red-600'>
          <UserX className='mr-2 h-4 w-4' />
          Reject Candidate
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
