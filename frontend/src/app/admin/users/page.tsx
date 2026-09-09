'use client'

import { useState, useEffect, useCallback } from 'react'
import { adminApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'

type User = {
  id: number
  email: string
  name: string
  companyName: string
  department: string
  videoCount: number
  isAdmin: boolean
  status: string
  createdAt: string
  lastLoginAt?: string
}

function UserDetailModal({
  user,
  onClose,
  onRoleChange,
  onDelete,
}: {
  user: User
  onClose: () => void
  onRoleChange: (role: 'manager' | 'member') => void
  onDelete: (deleteVideos: boolean) => void
}) {
  const [deleteVideos, setDeleteVideos] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [role, setRole] = useState<'manager' | 'member'>(user.isAdmin ? 'manager' : 'member')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative glass-card w-full max-w-lg p-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <h2 className="text-xl font-display font-bold text-[var(--color-text)] mb-6">사용자 정보</h2>

        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">이름</span>
            <span className="text-[var(--color-text)]">{user.name}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">이메일</span>
            <span className="text-[var(--color-text)]">{user.email}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">회사</span>
            <span className="text-[var(--color-text)]">{user.companyName}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">부서</span>
            <span className="text-[var(--color-text)]">{user.department}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">역할</span>
            {user.isAdmin ? (
              <span className="px-3 py-1.5 text-xs font-medium rounded-full bg-[var(--gradient-1)]/10 text-[var(--gradient-1)] border border-[var(--gradient-1)]/20">
                관리자
              </span>
            ) : (
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'manager' | 'member')}
                className="px-3 py-1.5 text-sm rounded-lg glass-input text-[var(--color-text)] cursor-pointer"
              >
                <option value="member">멤버</option>
                <option value="manager">매니저</option>
              </select>
            )}
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">가입일</span>
            <span className="text-[var(--color-text)]">{user.createdAt}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">영상 수</span>
            <span className="text-[var(--color-text)] font-display">{user.videoCount}개</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">상태</span>
            <span className={`px-3 py-1.5 text-xs font-medium rounded-full border ${
              user.status === 'active'
                ? 'bg-green-500/10 text-green-400 border-green-500/20'
                : user.status === 'suspended'
                ? 'bg-red-500/10 text-red-400 border-red-500/20'
                : 'bg-[var(--color-bg-muted)] text-[var(--color-text-secondary)] border-[var(--color-border)]'
            }`}>
              {user.status === 'active' ? '활성' : user.status === 'suspended' ? '정지' : '비활성'}
            </span>
          </div>
        </div>

        {showDeleteConfirm ? (
          <div className="mt-8 p-4 border border-red-500/20 rounded-xl bg-red-500/5">
            <p className="text-red-400 text-sm mb-4">정말 이 사용자를 삭제하시겠습니까?</p>
            <label className="flex items-center gap-2 mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={deleteVideos}
                onChange={(e) => setDeleteVideos(e.target.checked)}
                className="w-4 h-4 rounded border-[var(--color-border)] text-red-500 focus:ring-red-500"
              />
              <span className="text-[var(--color-text-secondary)] text-sm">영상도 함께 삭제</span>
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => onDelete(deleteVideos)}
                className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-red-500 text-white hover:bg-red-600 transition-colors"
              >
                삭제 확인
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 rounded-lg text-sm font-medium glass-card text-[var(--color-text)] hover:bg-[var(--color-bg-muted)] transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        ) : (
          <div className="flex gap-3 mt-8">
            {!user.isAdmin && role !== (user.isAdmin ? 'manager' : 'member') && (
              <button
                onClick={() => onRoleChange(role)}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-all"
                style={{ background: 'var(--gradient-1)' }}
              >
                역할 변경
              </button>
            )}
            {!user.isAdmin && (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="px-4 py-2.5 rounded-xl text-sm font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
              >
                삭제
              </button>
            )}
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium glass-card text-[var(--color-text)] hover:bg-[var(--color-bg-muted)] transition-colors"
            >
              닫기
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AdminUsersPage() {
  const { showToast } = useToast()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'admin' | 'user'>('all')
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true)
      const response = await adminApi.getUsers(1, 100, search || undefined)
      setUsers(response.items.map(u => ({
        id: u.account_id,
        email: u.email || '',
        name: u.member_name || '이름 없음',
        companyName: u.company_name || '-',
        department: u.department || '-',
        videoCount: u.video_count || 0,
        isAdmin: u.account_type === 'admin',
        status: u.status || 'active',
        createdAt: u.created_at?.split('T')[0] || '-',
        lastLoginAt: u.last_login_at?.split('T')[0],
      })))
    } catch (error) {
      showToast(error instanceof Error ? error.message : '사용자 로딩 실패', 'error')
    } finally {
      setLoading(false)
    }
  }, [search, showToast])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const handleSuspendUser = async (userId: number) => {
    try {
      await adminApi.updateUserStatus(userId, 'suspended')
      showToast('사용자가 정지되었습니다', 'success')
      fetchUsers()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '정지 처리 실패', 'error')
    }
  }

  const handleActivateUser = async (userId: number) => {
    try {
      await adminApi.updateUserStatus(userId, 'active')
      showToast('사용자가 활성화되었습니다', 'success')
      fetchUsers()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '활성화 처리 실패', 'error')
    }
  }

  const handleOpenDetail = async (user: User) => {
    try {
      const detail = await adminApi.getUserDetail(user.id)
      // 백엔드 응답이 nested 구조일 수 있음
      const isNested = detail.company !== undefined || detail.profile !== undefined
      setSelectedUser({
        id: detail.account_id,
        email: detail.email || '',
        name: isNested ? (detail.name || '이름 없음') : (detail.member_name || '이름 없음'),
        companyName: isNested ? (detail.company?.company_name || '-') : (detail.company_name || '-'),
        department: isNested ? (detail.profile?.department || '-') : (detail.department || '-'),
        videoCount: isNested ? (detail.statistics?.total_videos || 0) : (detail.video_count || 0),
        isAdmin: detail.account_type === 'admin',
        status: detail.status || (detail.is_active === false ? 'inactive' : 'active'),
        createdAt: isNested
          ? (detail.activity?.created_at?.split('T')[0] || '-')
          : (detail.created_at?.split('T')[0] || '-'),
        lastLoginAt: isNested
          ? detail.activity?.last_login_at?.split('T')[0]
          : detail.last_login_at?.split('T')[0],
      })
    } catch (error) {
      showToast(error instanceof Error ? error.message : '사용자 정보 로딩 실패', 'error')
    }
  }

  const handleRoleChange = async (role: 'manager' | 'member') => {
    if (!selectedUser) return
    try {
      await adminApi.updateUserRole(selectedUser.id, 1, role)
      showToast('역할이 변경되었습니다', 'success')
      setSelectedUser(null)
      fetchUsers()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '역할 변경 실패', 'error')
    }
  }

  const handleDeleteUser = async (deleteVideos: boolean) => {
    if (!selectedUser) return
    try {
      await adminApi.deleteUser(selectedUser.id, '관리자에 의한 삭제', deleteVideos)
      showToast('사용자가 삭제되었습니다', 'success')
      setSelectedUser(null)
      fetchUsers()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '삭제 실패', 'error')
    }
  }

  const filteredUsers = users.filter(u => {
    const matchesFilter = filter === 'all' || (filter === 'admin' ? u.isAdmin : !u.isAdmin)
    const matchesSearch = u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.companyName.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const totalUsers = users.filter(u => !u.isAdmin).length
  const adminCount = users.filter(u => u.isAdmin).length

  return (
    <div className="font-body">
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">사용자 관리</h1>
          <p className="text-[var(--color-text-secondary)]">등록된 사용자를 관리합니다</p>
        </div>
        <div className="flex gap-3">
          <div className="px-4 py-2 glass-card flex items-center gap-2">
            <span className="text-[var(--color-text-secondary)] text-sm">사용자</span>
            <span className="text-[var(--color-text)] font-display font-semibold">{totalUsers}</span>
          </div>
          <div className="px-4 py-2 glass-card flex items-center gap-2" style={{ borderColor: 'rgba(255, 107, 107, 0.2)' }}>
            <span className="text-[var(--gradient-1)] text-sm">관리자</span>
            <span className="text-[var(--gradient-1)] font-display font-semibold">{adminCount}</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-xs">
          <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="이름, 이메일, 회사명 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-2.5 glass-input text-[var(--color-text)] placeholder-[var(--color-text-tertiary)]"
          />
        </div>
        <div className="flex gap-2">
          {[
            { value: 'all', label: '전체', color: 'var(--gradient-5)' },
            { value: 'user', label: '일반 사용자', color: 'var(--gradient-3)' },
            { value: 'admin', label: '관리자', color: 'var(--gradient-1)' },
          ].map((item) => (
            <button
              key={item.value}
              onClick={() => setFilter(item.value as typeof filter)}
              className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                filter === item.value
                  ? 'text-white'
                  : 'glass-card text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
              }`}
              style={filter === item.value ? { background: item.color } : undefined}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden overflow-x-auto">
        <table className="w-full min-w-[900px]">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">사용자</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">이메일</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">회사/부서</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">권한</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">영상 수</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">가입일</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">액션</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">
            {filteredUsers.map((user) => (
              <tr key={user.id} className="hover:bg-[var(--color-bg-muted)]/50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer"
                      style={{
                        background: user.isAdmin
                          ? 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)'
                          : 'linear-gradient(135deg, var(--gradient-5)20 0%, var(--gradient-3)20 100%)'
                      }}
                      onClick={() => handleOpenDetail(user)}
                    >
                      <span className={`font-bold text-sm ${user.isAdmin ? 'text-white' : 'text-[var(--gradient-5)]'}`}>
                        {user.name.charAt(0)}
                      </span>
                    </div>
                    <button
                      onClick={() => handleOpenDetail(user)}
                      className="font-medium text-[var(--color-text)] hover:text-[var(--gradient-1)] transition-colors"
                    >
                      {user.name}
                    </button>
                  </div>
                </td>
                <td className="px-6 py-4 text-[var(--color-text-secondary)]">{user.email}</td>
                <td className="px-6 py-4">
                  <div>
                    <p className="text-[var(--color-text)] text-sm">{user.companyName}</p>
                    <p className="text-[var(--color-text-tertiary)] text-xs">{user.department}</p>
                  </div>
                </td>
                <td className="px-6 py-4">
                  {user.isAdmin ? (
                    <span className="px-3 py-1.5 text-xs font-medium rounded-full bg-[var(--gradient-1)]/10 text-[var(--gradient-1)] border border-[var(--gradient-1)]/20">
                      관리자
                    </span>
                  ) : (
                    <span className="px-3 py-1.5 text-xs font-medium rounded-full bg-[var(--color-bg-muted)] text-[var(--color-text-secondary)] border border-[var(--color-border)]">
                      사용자
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-[var(--color-text)] font-display">{user.videoCount}</td>
                <td className="px-6 py-4 text-[var(--color-text-secondary)]">{user.createdAt}</td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleOpenDetail(user)}
                      className="px-3 py-1.5 glass-card text-[var(--color-text)] text-sm rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
                    >
                      상세
                    </button>
                    {!user.isAdmin && (user.status === 'suspended' || user.status === 'inactive') && (
                      <button
                        onClick={() => handleActivateUser(user.id)}
                        className="px-3 py-1.5 bg-green-500/10 text-green-400 text-sm rounded-lg border border-green-500/20 hover:bg-green-500/20 transition-colors"
                      >
                        활성화
                      </button>
                    )}
                    {!user.isAdmin && user.status === 'active' && (
                      <button
                        onClick={() => handleSuspendUser(user.id)}
                        className="px-3 py-1.5 bg-red-500/10 text-red-400 text-sm rounded-lg border border-red-500/20 hover:bg-red-500/20 transition-colors"
                      >
                        정지
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredUsers.length === 0 && (
          <div className="p-12 text-center">
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4"
              style={{ background: 'linear-gradient(135deg, var(--gradient-5)10 0%, var(--gradient-3)10 100%)' }}
            >
              <svg className="w-8 h-8 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <p className="text-[var(--color-text-secondary)]">검색 결과가 없습니다</p>
          </div>
        )}
      </div>

      {selectedUser && (
        <UserDetailModal
          user={selectedUser}
          onClose={() => setSelectedUser(null)}
          onRoleChange={handleRoleChange}
          onDelete={handleDeleteUser}
        />
      )}
    </div>
  )
}
