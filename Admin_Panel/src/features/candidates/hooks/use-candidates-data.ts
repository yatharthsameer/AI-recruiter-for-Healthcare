import { useState, useEffect } from 'react'
import { type Candidate } from '../data/schema'
import { loadCandidatesFromApi } from '../data/candidates'

export function useCandidatesData() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCandidates = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await loadCandidatesFromApi()
      setCandidates(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load candidates')
      console.error('Error loading candidates:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCandidates()
  }, [])

  const refreshCandidates = () => {
    loadCandidates()
  }

  return {
    candidates,
    loading,
    error,
    refreshCandidates,
  }
}
