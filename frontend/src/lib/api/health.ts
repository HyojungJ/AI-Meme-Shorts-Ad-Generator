import { MOCK_MODE, API_URL_EXPORT } from './client'

// 백엔드 스키마와 일치하는 응답 타입
export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'mock' | 'error' | 'degraded'
  version?: string
  mode?: 'mock' | 'production'
  message?: string
}

export interface DatabaseHealthStatus {
  status: 'healthy' | 'unhealthy'
  database?: 'connected' | 'disconnected'
  connection?: string
  error?: string
}

export interface S3HealthStatus {
  status: 'healthy' | 'unhealthy' | 'mock' | 'error'
  s3?: string
  connection?: string
  bucket?: string
  region?: string
  message?: string
  error?: string
}

export interface FullHealthStatus {
  app: {
    status: 'healthy' | 'unhealthy'
    version: string
    mode: 'mock' | 'production'
  }
  database: {
    status: string
    connection: string
    error?: string
  }
  s3: {
    status: string
    connection: string
    bucket?: string
    region?: string
  }
  overall_status: 'healthy' | 'unhealthy'
}

export const healthApi = {
  async check(): Promise<HealthStatus> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 100))
      return {
        status: 'healthy',
        version: '1.0.0',
        mode: 'mock',
      }
    }

    const response = await fetch(`${API_URL_EXPORT}/api/v1/health`)
    if (!response.ok) {
      return { status: 'unhealthy', message: 'Health check failed' }
    }
    return response.json() as Promise<HealthStatus>
  },

  async checkDatabase(): Promise<DatabaseHealthStatus> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 100))
      return {
        status: 'healthy',
        database: 'connected',
      }
    }

    const response = await fetch(`${API_URL_EXPORT}/api/v1/health/db`)
    if (!response.ok) {
      return {
        status: 'unhealthy',
        database: 'disconnected',
        error: 'Database check failed',
      }
    }
    return response.json() as Promise<DatabaseHealthStatus>
  },

  async checkS3(): Promise<S3HealthStatus> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 100))
      return {
        status: 'healthy',
        s3: 'connected',
        bucket: 'mock-bucket',
        region: 'ap-northeast-2',
      }
    }

    const response = await fetch(`${API_URL_EXPORT}/api/v1/health/s3`)
    if (!response.ok) {
      return {
        status: 'unhealthy',
        error: 'S3 check failed',
      }
    }
    return response.json() as Promise<S3HealthStatus>
  },

  async checkAll(): Promise<FullHealthStatus> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      return {
        app: {
          status: 'healthy',
          version: '1.0.0',
          mode: 'mock',
        },
        database: {
          status: 'healthy',
          connection: 'connected',
        },
        s3: {
          status: 'healthy',
          connection: 'connected',
          bucket: 'mock-bucket',
          region: 'ap-northeast-2',
        },
        overall_status: 'healthy',
      }
    }

    const response = await fetch(`${API_URL_EXPORT}/api/v1/health/all`)
    if (!response.ok) {
      return {
        app: { status: 'unhealthy', version: 'unknown', mode: 'production' },
        database: { status: 'unhealthy', connection: 'disconnected' },
        s3: { status: 'unhealthy', connection: 'disconnected' },
        overall_status: 'unhealthy',
      }
    }
    return response.json() as Promise<FullHealthStatus>
  },
}
