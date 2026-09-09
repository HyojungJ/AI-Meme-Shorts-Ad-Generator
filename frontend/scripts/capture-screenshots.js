const puppeteer = require('puppeteer')
const fs = require('fs')
const path = require('path')

const BASE_URL = 'http://localhost:3000'
const OUTPUT_DIR = path.join(__dirname, '../docs/screenshots')

// 캡처할 페이지 목록
const pages = [
  // 공개 페이지
  { path: '/', name: '01_랜딩페이지', description: '서비스 소개 랜딩 페이지', auth: false },
  { path: '/login', name: '02_로그인', description: '로그인/회원가입 페이지', auth: false },
  { path: '/terms', name: '03_이용약관', description: '서비스 이용약관', auth: false },
  { path: '/privacy', name: '04_개인정보처리방침', description: '개인정보 처리방침', auth: false },

  // 사용자 페이지 (로그인 필요)
  { path: '/main', name: '05_대시보드', description: '메인 대시보드 - 통계 및 현황', auth: true },
  { path: '/user', name: '06_내영상목록', description: '사용자의 영상 목록', auth: true },
  { path: '/user/request', name: '07_영상제작요청', description: '새 영상 제작 요청 폼', auth: true },
  { path: '/user/video/1', name: '08_영상상세', description: '영상 상세 정보 및 시나리오 검수', auth: true },
  { path: '/profile', name: '09_프로필설정', description: '사용자 프로필 설정', auth: true },

  // 관리자 페이지
  { path: '/admin', name: '10_관리자대시보드', description: '관리자 메인 대시보드', auth: true, admin: true },
  { path: '/admin/analytics', name: '11_성과분석메인', description: '전체 성과 분석 요약', auth: true, admin: true },
  { path: '/admin/analytics/memes', name: '12_밈별분석', description: '밈 유형별 성과 비교', auth: true, admin: true },
  { path: '/admin/analytics/categories', name: '13_카테고리별분석', description: '카테고리별 성과 분석', auth: true, admin: true },
  { path: '/admin/analytics/trends', name: '14_트렌드분석', description: '트렌드 분석 및 예측', auth: true, admin: true },
  { path: '/admin/analytics/ab-tests', name: '15_AB테스트목록', description: 'A/B 테스트 목록', auth: true, admin: true },
  { path: '/admin/analytics/ab-tests/1', name: '16_AB테스트상세', description: 'A/B 테스트 상세 분석', auth: true, admin: true },
  { path: '/admin/videos', name: '17_영상관리', description: '전체 영상 관리', auth: true, admin: true },
  { path: '/admin/users', name: '18_사용자관리', description: '사용자 관리', auth: true, admin: true },
  { path: '/admin/settings', name: '19_시스템설정', description: '시스템 설정', auth: true, admin: true },
]

// 뷰포트 설정
const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
]

async function captureScreenshots() {
  console.log('🚀 스크린샷 캡처 시작...\n')

  // 출력 디렉토리 생성
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true })
  }

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  })

  const results = []

  for (const viewport of viewports) {
    const viewportDir = path.join(OUTPUT_DIR, viewport.name)
    if (!fs.existsSync(viewportDir)) {
      fs.mkdirSync(viewportDir, { recursive: true })
    }

    const page = await browser.newPage()
    await page.setViewport({ width: viewport.width, height: viewport.height })

    // 인증 토큰 먼저 설정 - 빈 페이지에서 시작
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle0', timeout: 30000 })

    // localStorage에 토큰 설정
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'mock_token_for_screenshots')
    })

    // 토큰 설정 확인
    const token = await page.evaluate(() => localStorage.getItem('access_token'))
    console.log(`🔑 인증 토큰 설정 완료 (${viewport.name}): ${token ? '성공' : '실패'}`)

    for (const pageInfo of pages) {
      const filename = `${pageInfo.name}_${viewport.name}.png`
      const filepath = path.join(viewportDir, filename)

      try {
        // 페이지 이동
        await page.goto(`${BASE_URL}${pageInfo.path}`, {
          waitUntil: 'networkidle0',
          timeout: 30000,
        })

        // 페이지 로딩 충분히 대기
        await new Promise(r => setTimeout(r, 2000))

        // 현재 URL 확인
        const currentUrl = page.url()

        // 리다이렉트 감지 시 토큰 재설정 후 재시도
        if (pageInfo.auth && (currentUrl.includes('/login') || currentUrl.includes('/_error'))) {
          console.log(`   ↪ ${pageInfo.name}: 리다이렉트 감지 (${currentUrl}), 재시도...`)

          // 토큰 재설정
          await page.evaluate(() => {
            localStorage.setItem('access_token', 'mock_token_for_screenshots')
          })

          // 페이지 새로고침
          await page.goto(`${BASE_URL}${pageInfo.path}`, {
            waitUntil: 'networkidle0',
            timeout: 30000,
          })

          await new Promise(r => setTimeout(r, 2000))
        }

        // 페이지 내용 확인 (404 체크)
        const pageTitle = await page.title()
        const is404 = pageTitle.includes('404') || await page.evaluate(() => {
          return document.body.innerText.includes('This page could not be found')
        })

        if (is404) {
          console.log(`⚠️  ${pageInfo.name} (${viewport.name}) - 404 감지`)
        }

        // 전체 페이지 스크롤하여 lazy load 트리거
        await autoScroll(page)

        // 맨 위로 스크롤
        await page.evaluate(() => window.scrollTo(0, 0))
        await new Promise(r => setTimeout(r, 500))

        // 스크린샷 촬영
        await page.screenshot({
          path: filepath,
          fullPage: true,
        })

        const fileSize = fs.statSync(filepath).size
        const status = fileSize > 20000 ? '✅' : '⚠️'
        console.log(`${status} ${pageInfo.name} (${viewport.name}) - ${Math.round(fileSize/1024)}KB`)

        results.push({
          ...pageInfo,
          viewport: viewport.name,
          filename,
          success: true,
        })
      } catch (error) {
        console.log(`❌ ${pageInfo.name} (${viewport.name}): ${error.message}`)
        results.push({
          ...pageInfo,
          viewport: viewport.name,
          filename,
          success: false,
          error: error.message,
        })
      }
    }

    await page.close()
  }

  await browser.close()

  // 화면 설계서 생성
  generateDesignDoc(results)

  console.log('\n✨ 완료!')
  console.log(`📁 스크린샷: ${OUTPUT_DIR}`)
  console.log(`📄 설계서: ${path.join(OUTPUT_DIR, '../화면설계서.md')}`)
}

async function autoScroll(page) {
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let totalHeight = 0
      const distance = 300
      const timer = setInterval(() => {
        const scrollHeight = document.body.scrollHeight
        window.scrollBy(0, distance)
        totalHeight += distance
        if (totalHeight >= scrollHeight) {
          clearInterval(timer)
          resolve()
        }
      }, 100)
    })
  })
}

function generateDesignDoc(results) {
  const docPath = path.join(OUTPUT_DIR, '../화면설계서.md')

  const grouped = {}
  for (const r of results) {
    if (!grouped[r.name]) grouped[r.name] = { ...r, viewports: {} }
    grouped[r.name].viewports[r.viewport] = r
  }

  let md = `# Meme-fluencer 화면 설계서

> 생성일: ${new Date().toLocaleDateString('ko-KR')}

---

## 목차

1. [공개 페이지](#1-공개-페이지)
2. [사용자 페이지](#2-사용자-페이지)
3. [관리자 페이지](#3-관리자-페이지)

---

## 1. 공개 페이지

로그인 없이 접근 가능한 페이지입니다.

`

  const publicPages = Object.values(grouped).filter(p => !p.auth)
  for (const p of publicPages) {
    md += generatePageSection(p)
  }

  md += `
---

## 2. 사용자 페이지

로그인한 사용자가 접근하는 페이지입니다.

`

  const userPages = Object.values(grouped).filter(p => p.auth && !p.admin)
  for (const p of userPages) {
    md += generatePageSection(p)
  }

  md += `
---

## 3. 관리자 페이지

관리자 권한이 필요한 페이지입니다.

`

  const adminPages = Object.values(grouped).filter(p => p.admin)
  for (const p of adminPages) {
    md += generatePageSection(p)
  }

  md += `
---

## 부록: 디자인 시스템

### 색상 팔레트

| 용도 | 색상 | 코드 |
|------|------|------|
| 배경 (Primary) | ⬛ | \`#0a0a0a\` |
| 배경 (Secondary) | ⬛ | \`#141414\` |
| 테두리 | ⬛ | \`#1a1a1a\` |
| 텍스트 (Primary) | ⬜ | \`#ffffff\` |
| 텍스트 (Secondary) | 🔘 | \`#888888\` |
| 텍스트 (Muted) | 🔘 | \`#555555\` |
| 액센트 (User) | 🟢 | \`#c8ff00\` |
| 액센트 (Admin) | 🔴 | \`#ef4444\` |

### 폰트

| 용도 | 폰트 |
|------|------|
| Display (제목) | Outfit |
| Body (본문) | Pretendard |

### 반응형 브레이크포인트

| 디바이스 | 너비 |
|----------|------|
| Desktop | 1440px |
| Tablet | 768px |
| Mobile | 390px |

---

*이 문서는 자동으로 생성되었습니다.*
`

  fs.writeFileSync(docPath, md, 'utf-8')
}

function generatePageSection(pageInfo) {
  const desktopImg = `./screenshots/desktop/${pageInfo.name}_desktop.png`
  const mobileImg = `./screenshots/mobile/${pageInfo.name}_mobile.png`

  return `
### ${pageInfo.name.replace(/^\d+_/, '')}

**경로**: \`${pageInfo.path}\`

**설명**: ${pageInfo.description}

| Desktop | Mobile |
|---------|--------|
| ![Desktop](${desktopImg}) | ![Mobile](${mobileImg}) |

---

`
}

// 실행
captureScreenshots().catch(console.error)
