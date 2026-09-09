import Link from 'next/link'

export const metadata = {
  title: '이용약관 - Admeme',
  description: 'Admeme 서비스 이용약관',
}

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[var(--color-bg)] font-body">
      <header className="border-b border-[var(--color-border)]">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <Link href="/" className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)' }}
            >
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <span className="font-bold text-[var(--color-text)] text-xl font-display">
              Admeme
            </span>
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-[var(--color-text)] mb-8">서비스 이용약관</h1>

        <div className="prose prose-invert max-w-none space-y-8 text-[var(--color-text-secondary)]">
          <p className="text-[var(--color-text-tertiary)]">
            시행일: 2026년 1월 1일
          </p>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제1조 (목적)</h2>
            <p>
              이 약관은 Admeme(이하 &quot;회사&quot;)가 제공하는 AI 영상 생성 서비스(이하 &quot;서비스&quot;)의
              이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항, 기타 필요한 사항을 규정함을 목적으로 합니다.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제2조 (정의)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>&quot;서비스&quot;란 회사가 제공하는 AI 기반 밈 영상 자동 생성 플랫폼을 말합니다.</li>
              <li>&quot;이용자&quot;란 이 약관에 따라 회사가 제공하는 서비스를 이용하는 회원 및 비회원을 말합니다.</li>
              <li>&quot;회원&quot;이란 회사에 개인정보를 제공하여 회원등록을 한 자로서, 회사의 서비스를 계속적으로 이용할 수 있는 자를 말합니다.</li>
              <li>&quot;콘텐츠&quot;란 서비스를 통해 생성된 영상, 시나리오 및 기타 결과물을 말합니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제3조 (약관의 효력 및 변경)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>이 약관은 서비스 화면에 게시하거나 기타의 방법으로 이용자에게 공지함으로써 효력이 발생합니다.</li>
              <li>회사는 필요한 경우 관련 법령을 위배하지 않는 범위에서 이 약관을 변경할 수 있습니다.</li>
              <li>변경된 약관은 적용일 7일 전부터 공지합니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제4조 (회원가입)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>이용자는 회사가 정한 가입 양식에 따라 회원정보를 기입한 후 이 약관에 동의한다는 의사표시를 함으로써 회원가입을 신청합니다.</li>
              <li>회사는 전항과 같이 회원으로 가입할 것을 신청한 이용자 중 다음 각 호에 해당하지 않는 한 회원으로 등록합니다.
                <ul className="list-disc pl-6 mt-2 space-y-1">
                  <li>가입신청자가 이 약관에 의하여 이전에 회원자격을 상실한 적이 있는 경우</li>
                  <li>등록 내용에 허위, 기재누락, 오기가 있는 경우</li>
                  <li>기타 회원으로 등록하는 것이 회사의 기술상 현저히 지장이 있다고 판단되는 경우</li>
                </ul>
              </li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제5조 (서비스의 제공 및 변경)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>회사는 다음과 같은 서비스를 제공합니다.
                <ul className="list-disc pl-6 mt-2 space-y-1">
                  <li>AI 기반 밈 영상 자동 생성</li>
                  <li>시나리오 생성 및 검수</li>
                  <li>영상 관리 및 다운로드</li>
                  <li>기타 회사가 정하는 서비스</li>
                </ul>
              </li>
              <li>회사는 서비스의 품질 향상을 위해 서비스의 내용을 변경할 수 있으며, 변경 시 사전에 공지합니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제6조 (서비스 이용료)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>서비스 이용료는 회사가 별도로 정하는 바에 따릅니다.</li>
              <li>회사는 유료 서비스 이용료를 변경할 수 있으며, 변경 시 30일 전에 공지합니다.</li>
              <li>결제 후 환불은 회사의 환불 정책에 따릅니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제7조 (콘텐츠의 저작권)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>서비스를 통해 생성된 콘텐츠의 저작권은 이용자에게 귀속됩니다.</li>
              <li>이용자는 생성된 콘텐츠를 자유롭게 상업적 목적으로 이용할 수 있습니다.</li>
              <li>단, 서비스 자체의 기술, 알고리즘, 소프트웨어에 대한 권리는 회사에 귀속됩니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제8조 (이용자의 의무)</h2>
            <p>이용자는 다음 행위를 하여서는 안 됩니다.</p>
            <ul className="list-disc pl-6 mt-4 space-y-2">
              <li>신청 또는 변경 시 허위 내용의 등록</li>
              <li>타인의 정보 도용</li>
              <li>회사가 게시한 정보의 변경</li>
              <li>회사가 정한 정보 이외의 정보(컴퓨터 프로그램 등)의 송신 또는 게시</li>
              <li>회사 및 기타 제3자의 저작권 등 지적재산권에 대한 침해</li>
              <li>회사 및 기타 제3자의 명예를 손상시키거나 업무를 방해하는 행위</li>
              <li>외설 또는 폭력적인 콘텐츠 생성 및 유포</li>
              <li>기타 불법적이거나 부당한 행위</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제9조 (회사의 의무)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>회사는 법령과 이 약관이 금지하거나 공서양속에 반하는 행위를 하지 않으며, 지속적이고 안정적으로 서비스를 제공하기 위해 최선을 다합니다.</li>
              <li>회사는 이용자의 개인정보를 보호하기 위해 보안시스템을 갖추어야 하며 개인정보처리방침을 공시하고 준수합니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제10조 (서비스 이용 제한)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>회사는 이용자가 이 약관의 의무를 위반하거나 서비스의 정상적인 운영을 방해한 경우, 서비스 이용을 제한할 수 있습니다.</li>
              <li>회사는 전항에 따른 이용 제한 시 사전에 통지합니다. 다만, 긴급한 경우에는 사후에 통지할 수 있습니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제11조 (회원 탈퇴 및 자격 상실)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>회원은 언제든지 회사에 탈퇴를 요청할 수 있으며, 회사는 즉시 회원탈퇴를 처리합니다.</li>
              <li>회원이 다음 각 호의 사유에 해당하는 경우, 회사는 회원자격을 제한 및 정지시킬 수 있습니다.
                <ul className="list-disc pl-6 mt-2 space-y-1">
                  <li>가입 신청 시에 허위 내용을 등록한 경우</li>
                  <li>서비스를 이용하여 법령 또는 이 약관이 금지하는 행위를 하는 경우</li>
                </ul>
              </li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제12조 (면책조항)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>회사는 천재지변 또는 이에 준하는 불가항력으로 인하여 서비스를 제공할 수 없는 경우에는 서비스 제공에 관한 책임이 면제됩니다.</li>
              <li>회사는 이용자의 귀책사유로 인한 서비스 이용의 장애에 대하여 책임을 지지 않습니다.</li>
              <li>회사는 AI가 생성한 콘텐츠의 정확성, 적합성에 대해 보증하지 않습니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">제13조 (분쟁해결)</h2>
            <ol className="list-decimal pl-6 space-y-2">
              <li>회사와 이용자 간에 발생한 분쟁에 관한 소송은 대한민국 법원을 관할법원으로 합니다.</li>
              <li>회사와 이용자 간에 제기된 소송에는 대한민국 법을 적용합니다.</li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">부칙</h2>
            <p>이 약관은 2026년 1월 1일부터 시행합니다.</p>
          </section>
        </div>

        <div className="mt-12 pt-8 border-t border-[var(--color-border)]">
          <Link href="/" className="text-[var(--gradient-1)] hover:underline">
            &larr; 홈으로 돌아가기
          </Link>
        </div>
      </main>
    </div>
  )
}
