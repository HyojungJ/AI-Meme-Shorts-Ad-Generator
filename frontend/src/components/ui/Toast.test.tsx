import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { ToastProvider, useToast } from './Toast'

function TestComponent() {
  const { showToast } = useToast()
  return (
    <div>
      <button onClick={() => showToast('Success message', 'success')}>Show Success</button>
      <button onClick={() => showToast('Error message', 'error')}>Show Error</button>
      <button onClick={() => showToast('Info message', 'info')}>Show Info</button>
    </div>
  )
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <TestComponent />
    </ToastProvider>
  )
}

describe('Toast', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders success toast when showToast is called with success type', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByText('Show Success'))
    expect(screen.getByText('Success message')).toBeInTheDocument()
  })

  it('renders error toast when showToast is called with error type', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByText('Show Error'))
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('renders info toast when showToast is called with info type', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByText('Show Info'))
    expect(screen.getByText('Info message')).toBeInTheDocument()
  })

  it('removes toast after 3 seconds', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByText('Show Success'))
    expect(screen.getByText('Success message')).toBeInTheDocument()

    await act(async () => {
      jest.advanceTimersByTime(3000)
    })

    expect(screen.queryByText('Success message')).not.toBeInTheDocument()
  })

  it('removes toast when close button is clicked', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByText('Show Success'))
    expect(screen.getByText('Success message')).toBeInTheDocument()

    const closeButton = screen.getByRole('button', { name: '알림 닫기' })
    await act(async () => {
      fireEvent.click(closeButton)
    })

    expect(screen.queryByText('Success message')).not.toBeInTheDocument()
  })
})

describe('useToast', () => {
  it('throws error when used outside ToastProvider', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

    function TestComponent() {
      useToast()
      return null
    }

    expect(() => render(<TestComponent />)).toThrow('useToast must be used within ToastProvider')
    consoleError.mockRestore()
  })
})
