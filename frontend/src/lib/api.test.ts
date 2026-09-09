import { setToken, removeToken, getVideos, addVideo, deleteVideo, getVideoById, updateVideo } from './api'

describe('Token management', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  it('setToken stores token in localStorage', () => {
    setToken('test_token')
    expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'test_token')
  })

  it('removeToken removes token from localStorage', () => {
    removeToken()
    expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
  })
})

describe('Video CRUD operations', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  describe('getVideos', () => {
    it('returns default videos when localStorage is empty', () => {
      ;(localStorage.getItem as jest.Mock).mockReturnValue(null)
      const videos = getVideos()
      expect(videos.length).toBeGreaterThan(0)
    })

    it('returns stored videos from localStorage', () => {
      const mockVideos = [{ id: '1', title: 'Test Video', status: 'pending' }]
      ;(localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockVideos))
      const videos = getVideos()
      expect(videos).toEqual(mockVideos)
    })
  })

  describe('addVideo', () => {
    it('adds a new video and returns it', () => {
      ;(localStorage.getItem as jest.Mock).mockReturnValue(null)
      const newVideo = addVideo({
        companyName: 'Test Company',
        productName: 'Test Product',
        productCategory: 'Electronics',
        productHighlight: 'Amazing features',
      })

      expect(newVideo.title).toBe('Test Product 홍보 영상')
      expect(newVideo.status).toBe('pending')
      expect(newVideo.companyName).toBe('Test Company')
      expect(localStorage.setItem).toHaveBeenCalled()
    })
  })

  describe('deleteVideo', () => {
    it('removes video from storage', () => {
      const mockVideos = [
        { id: '1', title: 'Video 1' },
        { id: '2', title: 'Video 2' },
      ]
      ;(localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockVideos))

      const result = deleteVideo('1')

      expect(result).toBe(true)
      expect(localStorage.setItem).toHaveBeenCalled()
    })
  })

  describe('getVideoById', () => {
    it('returns video when found', () => {
      const mockVideos = [{ id: '1', title: 'Test Video' }]
      ;(localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockVideos))

      const video = getVideoById('1')
      expect(video?.title).toBe('Test Video')
    })

    it('returns null when video not found', () => {
      ;(localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify([]))
      const video = getVideoById('nonexistent')
      expect(video).toBeNull()
    })
  })

  describe('updateVideo', () => {
    it('updates video with new data', () => {
      const mockVideos = [{ id: '1', title: 'Original Title', status: 'pending' }]
      ;(localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockVideos))

      const updated = updateVideo('1', { title: 'Updated Title' })

      expect(updated?.title).toBe('Updated Title')
      expect(localStorage.setItem).toHaveBeenCalled()
    })

    it('returns null when video not found', () => {
      ;(localStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify([]))
      const updated = updateVideo('nonexistent', { title: 'New' })
      expect(updated).toBeNull()
    })
  })
})
