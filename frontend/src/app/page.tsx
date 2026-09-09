'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { GradientMesh } from '@/components/ui/GradientMesh'

function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navLinks = [
    { href: '#features', label: 'Features' },
    { href: '#pricing', label: 'Pricing' },
    { href: '#faq', label: 'FAQ' },
  ]

  return (
    <>
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled ? 'bg-[var(--color-bg-card)] backdrop-blur-xl border-b border-[var(--color-border)]' : ''
      }`}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16 sm:h-20">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[var(--gradient-1)] to-[var(--gradient-4)] flex items-center justify-center shadow-lg shadow-[var(--gradient-1)]/20 group-hover:shadow-[var(--gradient-1)]/40 transition-shadow">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="font-display font-semibold text-lg text-[var(--color-text)]">Admeme</span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => (
                <a key={link.href} href={link.href} className="btn-ghost text-sm">
                  {link.label}
                </a>
              ))}
            </div>

            <div className="hidden md:flex items-center gap-3">
              <Link href="/login" className="btn-ghost text-sm">로그인</Link>
              <Link href="/login" className="btn-primary text-sm">시작하기</Link>
            </div>

            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 -mr-2"
              aria-label="메뉴"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </nav>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-[60] md:hidden">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <div className="absolute right-0 top-0 h-full w-80 glass-card rounded-none border-l p-6 animate-slide-in-right">
            <div className="flex justify-end mb-8">
              <button onClick={() => setMobileMenuOpen(false)} className="p-2 -mr-2">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <nav className="space-y-2 mb-8">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3.5 rounded-xl text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-muted)] hover:text-[var(--color-text)] transition-all font-display"
                >
                  {link.label}
                </a>
              ))}
            </nav>
            <div className="space-y-3">
              <Link href="/login" className="block w-full btn-secondary text-center">로그인</Link>
              <Link href="/login" className="block w-full btn-primary text-center">시작하기</Link>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function HeroSection() {
  return (
    <section className="relative pt-36 pb-24 sm:pt-44 sm:pb-32 overflow-hidden">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="badge badge-gradient mb-8 animate-fade-up">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--gradient-1)] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--gradient-1)]"></span>
            </span>
            AI-Powered Video Generation
          </div>

          <h1 className="heading-hero mb-8 animate-fade-up-1">
            밈 광고 영상,<br />
            <span className="text-gradient">자동으로</span> 만들어드립니다
          </h1>

          <p className="body-lg max-w-2xl mx-auto mb-12 animate-fade-up-2">
            제품 정보만 입력하면 AI가 트렌드를 분석하고<br className="hidden sm:block" />
            바이럴 영상을 자동으로 제작합니다
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-up-3">
            <Link href="/login" className="w-full sm:w-auto btn-primary text-base px-8">
              무료로 시작하기
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <a href="#features" className="w-full sm:w-auto btn-secondary text-base">
              더 알아보기
            </a>
          </div>
        </div>

      </div>
    </section>
  )
}

function FeaturesSection() {
  const features = [
    {
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'var(--gradient-3)',
      title: '빠른 제작',
      desc: '제품 정보 입력 후 AI가 시나리오부터 영상까지 자동 완료',
      extra: '평균 5분 내 완성',
    },
    {
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'var(--gradient-4)',
      title: '트렌드 분석',
      desc: '실시간 밈 트렌드 분석으로 최적의 바이럴 포맷 자동 선택',
    },
    {
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'var(--gradient-2)',
      title: '시나리오 검수',
      desc: '생성된 시나리오를 확인하고 수정 요청 가능',
    },
    {
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
      color: 'var(--gradient-1)',
      title: '다양한 밈 스타일',
      desc: '인기 밈 포맷을 활용한 영상 제작',
      memes: ['두둥탁', 'ASMR', '비포애프터', 'MZ플렉스'],
      span: 'md:col-span-2',
    },
    {
      icon: (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      ),
      color: 'var(--gradient-5)',
      title: '즉시 다운로드',
      desc: '완성된 영상을 고화질로 바로 다운로드',
    },
  ]

  return (
    <section id="features" className="relative py-24 sm:py-32">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-20">
          <p className="label mb-4">
            <span className="text-gradient">Features</span>
          </p>
          <h2 className="heading-1">
            왜 <span className="text-gradient">Admeme</span>인가요?
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <div
              key={i}
              className={`glass-card glow p-8 ${f.span || ''}`}
            >
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
                style={{ background: `linear-gradient(135deg, ${f.color}20 0%, ${f.color}40 100%)`, color: f.color }}
              >
                {f.icon}
              </div>
              <h3 className="heading-3 mb-3">{f.title}</h3>
              <p className="body-md">{f.desc}</p>

              {f.extra && (
                <div className="mt-6 pt-6 border-t border-[var(--color-border)]">
                  <div className="flex items-center gap-2 text-sm text-[var(--color-text-tertiary)]">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    {f.extra}
                  </div>
                </div>
              )}

              {f.memes && (
                <div className="mt-6 flex flex-wrap gap-2">
                  {f.memes.map((meme, j) => (
                    <span
                      key={j}
                      className="px-4 py-2 rounded-xl text-sm font-display font-medium"
                      style={{ background: `linear-gradient(135deg, ${f.color}10 0%, ${f.color}20 100%)`, color: f.color }}
                    >
                      {meme}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function HowItWorksSection() {
  const steps = [
    { num: '01', title: '정보 입력', desc: '회사와 제품 정보를 입력합니다', color: 'var(--gradient-1)' },
    { num: '02', title: 'AI 분석', desc: 'AI가 트렌드 분석 & 밈 선택', color: 'var(--gradient-4)' },
    { num: '03', title: '시나리오 검수', desc: '시나리오 확인 및 승인', color: 'var(--gradient-3)' },
    { num: '04', title: '영상 완성', desc: '영상 생성 & 다운로드', color: 'var(--gradient-5)' },
  ]

  return (
    <section className="relative py-24 sm:py-32">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-20">
          <p className="label mb-4">
            <span className="text-gradient">Process</span>
          </p>
          <h2 className="heading-1">
            간단한 <span className="text-gradient">4단계</span>
          </h2>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <div key={i} className="relative group">
              <div className="glass-card glow p-8 h-full">
                <div
                  className="text-5xl font-display font-bold mb-6"
                  style={{ color: step.color, opacity: 0.3 }}
                >
                  {step.num}
                </div>
                <h3 className="text-xl font-display font-semibold mb-3" style={{ color: step.color }}>
                  {step.title}
                </h3>
                <p className="body-sm">{step.desc}</p>
              </div>
              {i < steps.length - 1 && (
                <div className="hidden lg:flex absolute top-1/2 -right-3 transform -translate-y-1/2 z-10">
                  <svg className="w-6 h-6 text-[var(--color-border-strong)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function PricingSection() {
  const plans = [
    {
      name: 'Starter',
      price: '무료',
      desc: '처음 시작하는 분들을 위한',
      features: ['월 3개 영상', '기본 밈 스타일', '720p 화질', '이메일 지원'],
      cta: '무료로 시작',
      popular: false,
      color: 'var(--gradient-3)',
    },
    {
      name: 'Pro',
      price: '₩99,000',
      period: '/월',
      desc: '성장하는 비즈니스를 위한',
      features: ['월 20개 영상', '모든 밈 스타일', '1080p 화질', '우선 지원', '워터마크 제거'],
      cta: '시작하기',
      popular: true,
      color: 'var(--gradient-1)',
    },
    {
      name: 'Enterprise',
      price: '문의',
      desc: '대규모 팀을 위한',
      features: ['무제한 영상', '커스텀 밈', '4K 화질', '전담 매니저', 'API 연동'],
      cta: '문의하기',
      popular: false,
      color: 'var(--gradient-5)',
    },
  ]

  return (
    <section id="pricing" className="relative py-24 sm:py-32">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-20">
          <p className="label mb-4">
            <span className="text-gradient">Pricing</span>
          </p>
          <h2 className="heading-1">
            심플한 <span className="text-gradient">가격</span> 정책
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <div
              key={i}
              className={`glass-card gradient-border glow p-8 relative ${
                plan.popular ? 'ring-2 ring-[var(--gradient-1)] scale-105 z-10' : ''
              }`}
            >
              {plan.popular && (
                <div
                  className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 text-xs font-display font-semibold rounded-full text-white"
                  style={{ background: `linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)` }}
                >
                  인기
                </div>
              )}
              <div className="mb-8">
                <h3 className="text-xl font-display font-semibold mb-2" style={{ color: plan.color }}>{plan.name}</h3>
                <p className="body-sm">{plan.desc}</p>
              </div>
              <div className="mb-8">
                <span className="text-4xl font-display font-bold">{plan.price}</span>
                {plan.period && <span className="text-[var(--color-text-secondary)] font-body">{plan.period}</span>}
              </div>
              <ul className="space-y-4 mb-10">
                {plan.features.map((f, j) => (
                  <li key={j} className="flex items-center gap-3 text-sm font-body">
                    <div
                      className="w-5 h-5 rounded-full flex items-center justify-center"
                      style={{ background: `${plan.color}20` }}
                    >
                      <svg className="w-3 h-3" style={{ color: plan.color }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-[var(--color-text-secondary)]">{f}</span>
                  </li>
                ))}
              </ul>
              <button className={`w-full ${plan.popular ? 'btn-primary' : 'btn-secondary'}`}>
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function FAQSection() {
  const [open, setOpen] = useState<number | null>(null)
  const faqs = [
    { q: '영상 제작에 얼마나 걸리나요?', a: '제품 정보 입력 후 시나리오는 약 1분, 영상 완성까지는 약 5-10분 정도 소요됩니다.' },
    { q: '어떤 종류의 밈이 사용되나요?', a: 'AI가 실시간으로 인기 밈 트렌드를 분석하여 제품에 가장 적합한 밈 스타일을 자동으로 선택합니다.' },
    { q: '시나리오가 마음에 들지 않으면?', a: '시나리오 검수 단계에서 수정 요청을 할 수 있으며, AI가 피드백을 반영하여 새로운 시나리오를 생성합니다.' },
    { q: '영상 저작권은 누구에게 있나요?', a: '제작된 영상의 모든 저작권은 고객님에게 있습니다. 자유롭게 상업적 용도로 활용하실 수 있습니다.' },
  ]

  return (
    <section id="faq" className="relative py-24 sm:py-32">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <p className="label mb-4">
            <span className="text-gradient">FAQ</span>
          </p>
          <h2 className="heading-1">
            자주 묻는 <span className="text-gradient">질문</span>
          </h2>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <div key={i} className="glass-card overflow-hidden">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full px-6 py-5 flex items-center justify-between text-left"
              >
                <span className="font-display font-medium pr-4">{faq.q}</span>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                    open === i ? 'bg-[var(--gradient-1)] text-white rotate-180' : 'bg-[var(--color-bg-muted)]'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>
              {open === i && (
                <div className="px-6 pb-6 body-md animate-fade-in">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CTASection() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="glass-card gradient-border p-12 sm:p-16 text-center overflow-hidden relative">
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--gradient-1)] rounded-full filter blur-[100px]" />
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-[var(--gradient-4)] rounded-full filter blur-[100px]" />
          </div>
          <div className="relative z-10">
            <h2 className="heading-1 mb-6">
              지금 바로<br />
              <span className="text-gradient">시작하세요</span>
            </h2>
            <p className="body-lg max-w-xl mx-auto mb-10">
              무료로 시작하고, 첫 번째 밈 광고 영상을 만들어보세요
            </p>
            <Link href="/login" className="btn-primary text-base px-10 py-4">
              무료로 시작하기
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="relative py-12 border-t border-[var(--color-border)]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--gradient-1)] to-[var(--gradient-4)] flex items-center justify-center">
              <span className="text-white font-bold text-sm">A</span>
            </div>
            <span className="font-display font-medium">Admeme</span>
          </div>
          <nav className="flex items-center gap-8 text-sm font-body text-[var(--color-text-secondary)]">
            <Link href="/terms" className="hover:text-[var(--color-text)] transition-colors">이용약관</Link>
            <Link href="/privacy" className="hover:text-[var(--color-text)] transition-colors">개인정보처리방침</Link>
            <a href="mailto:support@admeme.com" className="hover:text-[var(--color-text)] transition-colors">문의하기</a>
          </nav>
          <p className="text-sm font-body text-[var(--color-text-tertiary)]">© 2026 Admeme</p>
        </div>
      </div>
    </footer>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen relative">
      <GradientMesh />
      <Navbar />
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <PricingSection />
      <FAQSection />
      <CTASection />
      <Footer />
    </div>
  )
}
