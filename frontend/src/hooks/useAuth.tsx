'use client'

import { useState, useEffect, createContext, useContext } from 'react'
import { authApi, setToken, removeTokens } from '@/lib/api'
import type { User } from '@/types'

type AuthContextType = {
  user: User | null
  loading: boolean
  loginWithEmail: (email: string, password: string) => Promise<User>
  register: (email: string, password: string, name: string, companyName: string, department: string) => Promise<User>
  logout: () => Promise<void>
  updateProfile: (data: { name?: string; companyName?: string; department?: string }) => Promise<User>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      authApi.getCurrentUser()
        .then((data) => setUser(data))
        .catch(() => {
          removeTokens()
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const loginWithEmail = async (email: string, password: string): Promise<User> => {
    const response = await authApi.login(email, password)
    setToken(response.access_token)
    const userData = await authApi.getCurrentUser()
    setUser(userData)
    return userData
  }

  const register = async (
    email: string,
    password: string,
    name: string,
    companyName: string,
    department: string
  ): Promise<User> => {
    const response = await authApi.register(email, password, name, companyName, department)
    if (response.access_token) {
      setToken(response.access_token)
    }
    const userData = await authApi.getCurrentUser()
    setUser(userData)
    return userData
  }

  const logout = async () => {
    await authApi.logout()
    setUser(null)
  }

  const updateProfile = async (data: { name?: string; companyName?: string; department?: string }): Promise<User> => {
    const backendData = {
      member_name: data.name,
      company_name: data.companyName,
      department: data.department,
    }
    const updatedUser = await authApi.updateProfile(backendData)
    setUser(updatedUser)
    return updatedUser
  }

  const refreshUser = async () => {
    const userData = await authApi.getCurrentUser()
    setUser(userData)
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginWithEmail, register, logout, updateProfile, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
