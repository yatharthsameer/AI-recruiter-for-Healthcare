import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { CandidatesDialogs } from './components/candidates-dialogs'
import { CandidatesPrimaryButtons } from './components/candidates-primary-buttons'
import { CandidatesProvider } from './components/candidates-provider'
import { CandidatesTable } from './components/candidates-table'
import { useCandidatesData } from './hooks/use-candidates-data'
import { Button } from '@/components/ui/button'
import { RefreshCw, AlertCircle } from 'lucide-react'

export function Candidates() {
  const { candidates, loading, error, refreshCandidates } = useCandidatesData()

  return (
    <CandidatesProvider>
      <Header fixed>
        <Search />
        <div className='ms-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </Header>

      <Main>
        <div className='mb-2 flex flex-wrap items-center justify-between space-y-2 gap-x-4'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Candidates</h2>
            <p className='text-muted-foreground'>
              Here&apos;s a list of interview candidates and their evaluations!
            </p>
            {error && (
              <div className='flex items-center space-x-2 text-red-600 text-sm mt-2'>
                <AlertCircle className='h-4 w-4' />
                <span>{error}</span>
              </div>
            )}
          </div>
          <div className='flex items-center space-x-2'>
            <Button
              variant="outline"
              size="sm"
              onClick={refreshCandidates}
              disabled={loading}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <CandidatesPrimaryButtons />
          </div>
        </div>
        <div className='-mx-4 flex-1 overflow-auto px-4 py-1 lg:flex-row lg:space-y-0 lg:space-x-12'>
          {loading ? (
            <div className='flex items-center justify-center h-64'>
              <div className='flex items-center space-x-2'>
                <RefreshCw className='h-6 w-6 animate-spin' />
                <span>Loading candidates...</span>
              </div>
            </div>
          ) : (
            <CandidatesTable data={candidates} />
          )}
        </div>
      </Main>

      <CandidatesDialogs />
    </CandidatesProvider>
  )
}
