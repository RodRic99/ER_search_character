import { Navigation } from "@/components/navigation"
import { SearchForm } from "@/components/search-form"
import { BarChart3, Clock, Shield } from "lucide-react"

const features = [
  {
    icon: BarChart3,
    title: "상세 통계",
    description: "승률, KDA, 챔피언별 통계 등 다양한 데이터 분석",
  },
  {
    icon: Clock,
    title: "실시간 업데이트",
    description: "최근 게임 전적을 실시간으로 확인",
  },
  {
    icon: Shield,
    title: "멀티 검색",
    description: "팀원 전체의 전적을 한 번에 분석",
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="mx-auto max-w-6xl px-4 py-12">
        <section className="flex flex-col items-center text-center">
          <h1 className="text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            게임 전적 분석
          </h1>
          <p className="mt-4 max-w-lg text-pretty text-lg text-muted-foreground">
            유저 닉네임을 입력하고 상세한 게임 전적과 통계를 확인하세요
          </p>
        </section>

        <section className="mx-auto mt-12 max-w-4xl">
          <SearchForm />
        </section>

        <section className="mt-20 grid gap-6 sm:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="group rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/50"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </section>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2026 StatTracker. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
