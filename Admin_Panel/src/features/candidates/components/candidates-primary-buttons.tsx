import { Download, FileText, BarChart3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useCandidates } from './candidates-provider'

export function CandidatesPrimaryButtons() {
  const { setOpen } = useCandidates()
  return (
    <div className='flex gap-2'>
      <Button
        variant='outline'
        className='space-x-1'
        onClick={() => setOpen('export')}
      >
        <span>Export</span> <Download size={18} />
      </Button>
      <Button
        variant='outline'
        className='space-x-1'
        onClick={() => window.open('/analytics', '_blank')}
      >
        <span>Analytics</span> <BarChart3 size={18} />
      </Button>
    </div>
  )
}
