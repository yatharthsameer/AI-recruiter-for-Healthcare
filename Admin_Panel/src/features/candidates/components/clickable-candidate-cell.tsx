import { useNavigate } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { type Candidate } from '../data/schema'
import { positions } from '../data/data'

interface ClickableCandidateCellProps {
  candidate: Candidate
}

export function ClickableCandidateCell({ candidate }: ClickableCandidateCellProps) {
  const navigate = useNavigate()
  const position = positions.find((pos) => pos.value === candidate.position)

  const handleClick = () => {
    navigate({ to: '/candidates/$candidateId', params: { candidateId: candidate.id } })
  }

  return (
    <div className="flex flex-col space-y-1">
      <Button 
        variant="ghost" 
        className="justify-start p-0 h-auto font-medium text-left hover:text-primary"
        onClick={handleClick}
      >
        {candidate.candidateName}
      </Button>
      <div className="text-sm text-muted-foreground">{candidate.email}</div>
      {position && (
        <Badge variant="outline" className="w-fit text-xs">
          {position.label}
        </Badge>
      )}
    </div>
  )
}
