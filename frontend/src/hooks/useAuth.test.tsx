import { render, screen, waitFor, act } from '@testing-library/react'
import { AuthProvider, useAuth } from './useAuth'
import * as api from '@/lib/api'

const mockGetCurrentUser = jest.fn()
const mockLogin = jest.fn()
const mockLogout = jest.fn()

jest.mock('@/lib/api', () => ({
  authApi: {
    getCurrentUser: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
  },
  setToken: jest.fn(),
  removeToken: jest.fn(),
  removeTokens: jest.fn(),
}))

function TestComponent() {
  const { user, loading, logout } = useAuth()

  if (loading) return <div>Loading...</div>
  if (!user) return <div>Not logged in</div>

  return (
    <div>
      <span>User: {user.email}</span>
      <button onClick={logout}>Logout</button>
    </div>
  )
}

function renderWithProvider() {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  it('shows loading state initially', async () => {
    ;(localStorage.getItem as jest.Mock).mockReturnValue(null)
    renderWithProvider()

    await waitFor(() => {
      expect(screen.getByText('Not logged in')).toBeInTheDocument()
    })
  })

  it('loads user from token on mount', async () => {
    ;(localStorage.getItem as jest.Mock).mockReturnValue('valid_token')
    ;(api.authApi.getCurrentUser as jest.Mock).mockResolvedValue({
      user_id: 1,
      email: 'test@example.com',
      nickname: 'Test User',
    })

    renderWithProvider()

    await waitFor(() => {
      expect(screen.getByText('User: test@example.com')).toBeInTheDocument()
    })
  })

  it('clears user when token is invalid', async () => {
    ;(localStorage.getItem as jest.Mock).mockReturnValue('invalid_token')
    ;(api.authApi.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Invalid token'))

    renderWithProvider()

    await waitFor(() => {
      expect(screen.getByText('Not logged in')).toBeInTheDocument()
      expect(api.removeTokens).toHaveBeenCalled()
    })
  })
})

describe('useAuth', () => {
  it('throws error when used outside AuthProvider', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

    function TestComponent() {
      useAuth()
      return null
    }

    expect(() => render(<TestComponent />)).toThrow('useAuth must be used within AuthProvider')
    consoleError.mockRestore()
  })
})

describe('logout', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('clears user and removes token', async () => {
    ;(localStorage.getItem as jest.Mock).mockReturnValue('valid_token')
    ;(api.authApi.getCurrentUser as jest.Mock).mockResolvedValue({
      user_id: 1,
      email: 'test@example.com',
      nickname: 'Test User',
    })
    ;(api.authApi.logout as jest.Mock).mockResolvedValue(undefined)

    renderWithProvider()

    await waitFor(() => {
      expect(screen.getByText('User: test@example.com')).toBeInTheDocument()
    })

    await act(async () => {
      screen.getByText('Logout').click()
    })

    await waitFor(() => {
      expect(screen.getByText('Not logged in')).toBeInTheDocument()
    })
  })
})
