import { api, MOCK_MODE } from '../client'

export const characterApi = {
  async suggestCharacterPrompts(data: {
    product_name: string
    product_category?: string
    product_description?: string
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 400))
      return {
        character_image_prompt: `A friendly mascot character for ${data.product_name}, cheerful mood, clean illustration style, full body shot, soft lighting.`,
        character_voice_prompt: 'A warm, friendly voice with an upbeat and approachable tone.',
      }
    }

    return api.post<{
      character_image_prompt: string
      character_voice_prompt: string
    }>('/api/v1/videos/characters/prompts', data)
  },
}
