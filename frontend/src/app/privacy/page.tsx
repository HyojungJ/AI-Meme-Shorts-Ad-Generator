import Link from 'next/link'

export const metadata = {
  title: '개인정보처리방침 - Admeme',
  description: 'Admeme 개인정보처리방침',
}

export default function PrivacyPage() {
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
        <h1 className="text-3xl font-bold text-[var(--color-text)] mb-8">개인정보처리방침</h1>

        <div className="prose prose-invert max-w-none space-y-8 text-[var(--color-text-secondary)]">
          <p className="text-[var(--color-text-tertiary)]">
            시행일: 2026년 1월 1일
          </p>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">1. 개인정보의 수집 및 이용 목적</h2>
            <p>
              Admeme(이하 &quot;회사&quot;)는 다음의 목적을 위하여 개인정보를 처리합니다.
              처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며,
              이용 목적이 변경되는 경우에는 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.
            </p>
            <ul className="list-disc pl-6 mt-4 space-y-2">
              <li>회원 가입 및 관리: 회원제 서비스 이용에 따른 본인확인, 개인식별, 불량회원의 부정이용 방지</li>
              <li>서비스 제공: AI 영상 생성 서비스 제공, 콘텐츠 제공, 맞춤 서비스 제공</li>
              <li>고객 지원: 민원처리, 고지사항 전달</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">2. 수집하는 개인정보 항목</h2>
            <p>회사는 서비스 제공을 위해 다음과 같은 개인정보를 수집합니다.</p>
            <ul className="list-disc pl-6 mt-4 space-y-2">
              <li>필수항목: 이메일 주소, 비밀번호, 닉네임</li>
              <li>Google 로그인 시: 이메일 주소, 프로필 이미지, 이름</li>
              <li>자동 수집 항목: 접속 IP, 쿠키, 서비스 이용 기록, 접속 로그</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">3. 개인정보의 보유 및 이용 기간</h2>
            <p>
              회사는 법령에 따른 개인정보 보유·이용 기간 또는 정보주체로부터 개인정보를 수집 시에
              동의받은 개인정보 보유·이용 기간 내에서 개인정보를 처리·보유합니다.
            </p>
            <ul className="list-disc pl-6 mt-4 space-y-2">
              <li>회원 정보: 회원 탈퇴 시까지 (단, 관계 법령에 따라 보존할 필요가 있는 경우 해당 기간)</li>
              <li>서비스 이용 기록: 3년</li>
              <li>로그인 기록: 3개월</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">4. 개인정보의 파기 절차 및 방법</h2>
            <p>
              회사는 개인정보 보유 기간의 경과, 처리목적 달성 등 개인정보가 불필요하게 되었을 때에는
              지체 없이 해당 개인정보를 파기합니다.
            </p>
            <ul className="list-disc pl-6 mt-4 space-y-2">
              <li>전자적 파일 형태: 기록을 재생할 수 없는 기술적 방법 사용</li>
              <li>종이 문서: 분쇄기로 분쇄하거나 소각</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">5. 개인정보의 제3자 제공</h2>
            <p>
              회사는 정보주체의 개인정보를 제1조에서 명시한 범위 내에서만 처리하며,
              정보주체의 동의, 법률의 특별한 규정 등에 해당하는 경우에만 개인정보를 제3자에게 제공합니다.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">6. 정보주체의 권리·의무 및 행사방법</h2>
            <p>정보주체는 회사에 대해 언제든지 다음 각 호의 개인정보 보호 관련 권리를 행사할 수 있습니다.</p>
            <ul className="list-disc pl-6 mt-4 space-y-2">
              <li>개인정보 열람 요구</li>
              <li>오류 등이 있을 경우 정정 요구</li>
              <li>삭제 요구</li>
              <li>처리정지 요구</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">7. 쿠키의 사용</h2>
            <p>
              회사는 이용자에게 개별적인 맞춤 서비스를 제공하기 위해 이용정보를 저장하고
              수시로 불러오는 &apos;쿠키(cookie)&apos;를 사용합니다. 쿠키는 웹사이트가
              고객의 컴퓨터 브라우저에 전송하는 소량의 정보입니다.
            </p>
            <ul className="list-disc pl-6 mt-4 space-y-2">
              <li>쿠키의 사용 목적: 로그인 상태 유지, 서비스 이용 통계</li>
              <li>쿠키 설정 거부 방법: 브라우저 설정에서 쿠키를 차단할 수 있습니다</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">8. 개인정보 보호책임자</h2>
            <p>
              회사는 개인정보 처리에 관한 업무를 총괄해서 책임지고,
              개인정보 처리와 관련한 정보주체의 불만처리 및 피해구제 등을 위하여
              아래와 같이 개인정보 보호책임자를 지정하고 있습니다.
            </p>
            <div className="mt-4 p-4 glass-card">
              <p className="text-[var(--color-text)]">개인정보 보호책임자</p>
              <p className="text-[var(--color-text-secondary)] mt-2">이메일: privacy@admeme.com</p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-[var(--color-text)] mb-4">9. 개인정보처리방침의 변경</h2>
            <p>
              이 개인정보처리방침은 시행일로부터 적용되며, 법령 및 방침에 따른 변경내용의 추가,
              삭제 및 정정이 있는 경우에는 변경사항의 시행 7일 전부터 공지사항을 통하여 고지할 것입니다.
            </p>
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
