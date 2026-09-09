import { videoApi as crudVideoApi } from './crud'
import { characterApi } from './character'

// Merge suggestCharacterPrompts into videoApi for backward compatibility
export const videoApi = {
  ...crudVideoApi,
  suggestCharacterPrompts: characterApi.suggestCharacterPrompts,
}

export { scenarioApi } from './scenario'
export { statusApi } from './status'
