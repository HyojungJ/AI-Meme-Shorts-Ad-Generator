import { api } from './client'

export interface CharacterProfile {
  id: string
  name: string
  subtitle: string
  emoji: string
  appearance: string
  voice: string
  full_description: string
  image_url: string
  audio_url: string
}

export const characterProfilesApi = {
  /**
   * 캐릭터 프로필 목록 조회
   */
  getProfiles: async (): Promise<CharacterProfile[]> => {
    const profiles = await api.get<CharacterProfile[]>('/api/v1/character-profiles')
    return profiles
  }
}
