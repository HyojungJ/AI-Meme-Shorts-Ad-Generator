import { logger } from '@/lib/logger'
import type { Video, MyProjectWorkflowResponse, ProjectResponse } from '@/types'

export function transformProjectToVideo(project: ProjectResponse & { character_id?: number; scenes?: Array<{ scene_number: number; content: string; timestamp?: string }> }): Video {
  return {
    id: String(project.ad_id),
    title: project.title,
    status: project.status as Video['status'],
    views: project.views || 0,
    createdAt: project.created_at.split('T')[0],
    companyName: project.company_name,
    productCategory: project.product_category,
    productHighlight: project.product_highlight,
    productImageUrl: project.product_image_url || undefined,
    characterImagePrompt: project.character_style,
    memeType: project.meme_type as Video['memeType'],
    characterImageUrl: project.character_image_url || undefined,
    voiceSampleUrl: project.voice_sample_url || undefined,
    characterId: project.character_id,
    videoUrl: project.video_url || undefined,
    scenes: project.scenes,
  }
}

export function transformWorkflowToVideo(workflow: MyProjectWorkflowResponse): Video {
  const statusMap: Record<string, Video['status']> = {
    'draft': 'pending',
    'created': 'pending',
    'generating_character': 'character_generating',
    'generating_voice': 'voice_generating',
    'pending_approval': 'character_review',
    'generating_scenario': 'scenario_generating',
    'content_generating': 'scenario_generating',
    'generating_video': 'video_generating',
    'completed': 'completed',
    'failed': 'failed',
  }

  let mappedStatus = statusMap[workflow.status] || 'character_generating'

  // current_stage 기반으로 더 정확한 상태 매핑
  if (workflow.current_stage) {
    const stage = workflow.current_stage.toLowerCase()

    if (workflow.status === 'pending_approval') {
      if (stage.includes('video') || stage.includes('scenario')) {
        mappedStatus = 'video_review'  // 영상 검수
      } else if (stage.includes('character') || stage.includes('voice')) {
        mappedStatus = 'character_review'  // 캐릭터 검수
      }
    }
  }

  logger.debug('VideoAPI', `[TRANSFORM] ad_id=${workflow.ad_id}, status=${workflow.status}, stage=${workflow.current_stage}, mapped=${mappedStatus}`)

  return {
    id: String(workflow.ad_id),
    title: workflow.item_name || '제목 없음',
    status: mappedStatus,
    views: 0,
    createdAt: workflow.created_at.split('T')[0],
    characterId: workflow.character_id,
    sceneImageUrl: workflow.scene_image_url || undefined,
  }
}
