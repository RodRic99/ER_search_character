import { Navigation } from "@/components/navigation"
import { SearchForm } from "@/components/search-form"
import { BarChart3, Clock, Shield } from "lucide-react"

const features = [
  {
    icon: BarChart3,
    title: "조합 찾기의 편리함",
    description: "무슨 캐릭터를 할지 고민될때 가장 궁합이 좋은 캐릭터를 추천합니다!",
  },
  {
    icon: Clock,
    title: "Fast look",
    description: "Search one to three players and review the recommended trio instantly.",
  },
  {
    icon: Shield,
    title: "Team synergy",
    description: "Compare combinations and spot safer, higher-value team setups.",
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="mx-auto max-w-6xl px-4 py-12">
        <section className="flex flex-col items-center text-center">
          <h1 className="text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            이터널리턴 조합 추천기
          </h1>
          <p className="mt-4 max-w-2xl text-pretty text-lg text-muted-foreground">
            플레이어를 조회하여 모스트중 가장 궁합이좋은 조합을 추천합니다!!

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
          <p>&copy; 2026 이리메타. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
