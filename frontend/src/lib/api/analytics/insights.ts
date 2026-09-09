import { hourlyViewsDistribution } from '../mock'
import type {
  MemePerformance,
  CategoryPerformance,
  TrendDataPoint,
  TrendInsight,
} from '@/types'
import { INSIGHT_THRESHOLDS } from '@/lib/constants/thresholds'

export function generateInsights(
  memeData: MemePerformance[],
  categoryData: CategoryPerformance[],
  trends: TrendDataPoint[],
  summary: { viewsChange: number; totalViews: number }
): TrendInsight[] {
  const insights: TrendInsight[] = []

  // 1. 조회수 증감률 기반 인사이트
  if (summary.viewsChange > INSIGHT_THRESHOLDS.GREAT_INCREASE) {
    insights.push({
      type: 'positive',
      title: `조회수 ${summary.viewsChange}% 상승`,
      description: `지난 7일간 총 조회수가 ${summary.viewsChange}% 증가했습니다. 현재 추세가 매우 좋습니다.`,
    })
  } else if (summary.viewsChange > INSIGHT_THRESHOLDS.GOOD_INCREASE) {
    insights.push({
      type: 'positive',
      title: `조회수 ${summary.viewsChange}% 상승`,
      description: `지난 7일간 조회수가 안정적으로 증가하고 있습니다.`,
    })
  } else if (summary.viewsChange < INSIGHT_THRESHOLDS.CONCERNING_DECREASE) {
    insights.push({
      type: 'negative',
      title: '조회수 감소 주의',
      description: `지난 7일간 조회수가 ${Math.abs(summary.viewsChange)}% 감소했습니다. 콘텐츠 전략 점검이 필요합니다.`,
    })
  }

  // 2. 최고 성과 밈 (조회수 기준)
  if (memeData.length > 0) {
    const topMeme = [...memeData].sort((a, b) => b.avgViews - a.avgViews)[0]
    const avgViews = memeData.reduce((sum, m) => sum + m.avgViews, 0) / memeData.length
    const outperformance = Math.round(((topMeme.avgViews - avgViews) / avgViews) * 100)

    if (outperformance > 20) {
      insights.push({
        type: 'positive',
        title: `'${topMeme.label}' 밈 조회수 최고`,
        description: `평균 조회수 ${topMeme.avgViews.toLocaleString()}회로 전체 밈 평균 대비 ${outperformance}% 높습니다.`,
      })
    }

    // 최고 완료율 밈
    const topCompletionMeme = [...memeData].sort((a, b) => b.avgCompletionRate - a.avgCompletionRate)[0]
    if (topCompletionMeme.avgCompletionRate >= 80) {
      insights.push({
        type: 'positive',
        title: `'${topCompletionMeme.label}' 완료율 ${topCompletionMeme.avgCompletionRate}%`,
        description: `시청 완료율이 가장 높아 끝까지 시청하는 비율이 우수합니다.`,
      })
    }
  }

  // 3. 카테고리별 트렌드 분석
  const downCategories = categoryData.filter(c => c.trend === 'down')
  if (downCategories.length > 0) {
    const worstCategory = downCategories.sort((a, b) => a.avgViews - b.avgViews)[0]
    insights.push({
      type: 'negative',
      title: `'${worstCategory.category}' 조회수 하락`,
      description: `해당 카테고리의 조회수가 감소 추세입니다. 밈 유형 변경을 권장합니다.`,
    })
  }

  // 4. 시간대 분석 (hourlyViewsDistribution 기반)
  const peakHours = hourlyViewsDistribution
    .filter(h => h.percent >= INSIGHT_THRESHOLDS.PEAK_HOUR_MIN_PERCENT)
    .map(h => h.hour)
  if (peakHours.length > 0) {
    const peakStart = Math.min(...peakHours)
    const peakEnd = Math.max(...peakHours)
    const peakPercent = hourlyViewsDistribution
      .filter(h => h.hour >= peakStart && h.hour <= peakEnd)
      .reduce((sum, h) => sum + h.percent, 0)

    insights.push({
      type: 'neutral',
      title: '조회수 피크 시간대',
      description: `${peakStart}시-${peakEnd + 1}시에 전체 조회의 ${Math.round(peakPercent)}%가 발생합니다. 이 시간대 업로드를 권장합니다.`,
    })
  }

  // 5. 일평균 조회수 계산
  const actualTrends = trends.filter(t => !t.predicted)
  if (actualTrends.length >= 14) {
    const recentWeek = actualTrends.slice(-7)
    const prevWeek = actualTrends.slice(-14, -7)
    const recentAvg = recentWeek.reduce((sum, t) => sum + t.views, 0) / 7
    const prevAvg = prevWeek.reduce((sum, t) => sum + t.views, 0) / 7
    const dailyGrowth = Math.round(((recentAvg - prevAvg) / prevAvg) * 100)

    if (dailyGrowth > 15) {
      insights.push({
        type: 'positive',
        title: '일평균 조회수 상승',
        description: `일평균 조회수가 ${prevAvg.toLocaleString()}회에서 ${recentAvg.toLocaleString()}회로 ${dailyGrowth}% 증가했습니다.`,
      })
    }
  }

  // 최대 5개만 반환
  return insights.slice(0, 5)
}
