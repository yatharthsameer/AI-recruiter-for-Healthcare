import React, { useState } from 'react'
import useDialogState from '@/hooks/use-dialog-state'
import { type Candidate } from '../data/schema'

type CandidatesDialogType = 'view' | 'update' | 'delete' | 'export' | 'transcript'

type CandidatesContextType = {
  open: CandidatesDialogType | null
  setOpen: (str: CandidatesDialogType | null) => void
  currentRow: Candidate | null
  setCurrentRow: React.Dispatch<React.SetStateAction<Candidate | null>>
}

const CandidatesContext = React.createContext<CandidatesContextType | null>(null)

export function CandidatesProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useDialogState<CandidatesDialogType>(null)
  const [currentRow, setCurrentRow] = useState<Candidate | null>(null)

  return (
    <CandidatesContext value={{ open, setOpen, currentRow, setCurrentRow }}>
      {children}
    </CandidatesContext>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useCandidates = () => {
  const candidatesContext = React.useContext(CandidatesContext)

  if (!candidatesContext) {
    throw new Error('useCandidates has to be used within <CandidatesContext>')
  }

  return candidatesContext
}
