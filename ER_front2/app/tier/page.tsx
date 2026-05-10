"use client"

import { useEffect, useMemo, useState } from "react"
import { Navigation } from "@/components/navigation"
import { getCharacterImage, getCharacterWeaponCode } from "@/lib/characters"
import { cn } from "@/lib/utils"
import { getApiBaseUrl } from "@/lib/api-base-url"
import { ArrowDown, ArrowUp, Loader2, TrendingUp } from "lucide-react"
import { CharacterAvatar } from "@/components/character-avatar"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface TierListEntry {
  rank: number
  characterNum: number
  characterName: string
  tier: string
  rpGain: number
  pickRate: number
  winRate: number
  top3Rate: number
  averageRank: number
  averageDamage: number
  averageTakenDamage: number
  averagePlayerKill: number
}

interface TierListResponse {
  windowStart: string
  windowEnd: string
  days: number
  entries: TierListEntry[]
}

type RankTierFilter = "diamond" | "meteor" | "mithril"
type WindowFilter = "1" | "2"
type SortDirection = "desc" | "asc"
type SortKey =
  | "rank"
  | "characterName"
  | "tier"
  | "rpGain"
  | "pickRate"
  | "winRate"
  | "top3Rate"
  | "averageRank"
  | "averageDamage"
  | "averageTakenDamage"
  | "averagePlayerKill"

const apiBaseUrl = getApiBaseUrl()

const tierStyles: Record<string, string> = {
  S: "bg-cyan-400/15 text-cyan-300 ring-1 ring-cyan-400/40",
  A: "bg-emerald-400/15 text-emerald-300 ring-1 ring-emerald-400/40",
  B: "bg-amber-400/15 text-amber-300 ring-1 ring-amber-400/40",
  C: "bg-violet-400/15 text-violet-300 ring-1 ring-violet-400/40",
  D: "bg-zinc-400/15 text-zinc-300 ring-1 ring-zinc-400/40",
}

const tierSortOrder: Record<string, number> = {
  S: 0,
  A: 1,
  B: 2,
  C: 3,
  D: 4,
}

const percentFormatter = new Intl.NumberFormat("ko-KR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const numberFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 0,
})

const decimalFormatter = new Intl.NumberFormat("ko-KR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export default function TierPage() {
  const [data, setData] = useState<TierListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rankTierFilter, setRankTierFilter] = useState<RankTierFilter>("diamond")
  const [windowFilter, setWindowFilter] = useState<WindowFilter>("1")
  const [sortKey, setSortKey] = useState<SortKey>("tier")
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc")

  useEffect(() => {
    let mounted = true

    const loadTierList = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetch(
          `${apiBaseUrl}/api/tier-list?rankTier=${rankTierFilter}&week=${windowFilter}`
        )
        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`)
        }

        const responseData: TierListResponse = await response.json()
        if (mounted) {
          setData(responseData)
        }
      } catch (requestError) {
        if (mounted) {
          setError(requestError instanceof Error ? requestError.message : "Request failed.")
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    loadTierList()

    return () => {
      mounted = false
    }
  }, [rankTierFilter, windowFilter])

  const sortedEntries = useMemo(() => {
    const entries = data?.entries ? [...data.entries] : []
    return entries.sort((left, right) => {
      const direction = sortDirection === "asc" ? 1 : -1

      if (sortKey === "tier") {
        const leftTierOrder = tierSortOrder[left.tier] ?? Number.MAX_SAFE_INTEGER
        const rightTierOrder = tierSortOrder[right.tier] ?? Number.MAX_SAFE_INTEGER

        if (leftTierOrder !== rightTierOrder) {
          return (leftTierOrder - rightTierOrder) * direction
        }

        return (left.rank - right.rank) * direction
      }

      if (sortKey === "characterName" || sortKey === "tier") {
        return left[sortKey].localeCompare(right[sortKey], "ko") * direction
      }

      return ((left[sortKey] as number) - (right[sortKey] as number)) * direction
    })
  }, [data, sortDirection, sortKey])

  const topEntries = useMemo(() => sortedEntries.slice(0, 3), [sortedEntries])
  const filterLabel =
    rankTierFilter === "mithril"
      ? "Mithril+"
      : rankTierFilter === "meteor"
        ? "Meteor"
        : "Diamond"
  const sortLabel = sortDirection === "asc" ? "오름차순" : "내림차순"
  const windowLabel = windowFilter === "2" ? "2주 전" : "1주 전"

  const handleSortChange = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((currentDirection) =>
        currentDirection === "asc" ? "desc" : "asc"
      )
      return
    }

    setSortKey(key)
    setSortDirection("desc")
  }

  const SortButtons = ({ column }: { column: SortKey }) => (
    <button
      type="button"
      onClick={() => handleSortChange(column)}
      className={cn(
        "ml-1 inline-flex items-center rounded p-0.5 align-middle text-zinc-500 transition-colors hover:bg-white/10 hover:text-zinc-100",
        sortKey === column && "bg-white/10 text-cyan-300"
      )}
      aria-label={`${column} sort ${sortKey === column ? sortDirection : "desc"}`}
    >
      {sortKey === column && sortDirection === "asc" ? (
        <ArrowUp className="h-3 w-3" />
      ) : (
        <ArrowDown className="h-3 w-3" />
      )}
    </button>
  )

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />

      <main className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.16),transparent_32%),radial-gradient(circle_at_80%_20%,rgba(251,191,36,0.12),transparent_22%)]" />

        <div className="relative mx-auto max-w-7xl px-4 py-10">
          <section className="rounded-[28px] border border-white/10 bg-zinc-950/80 p-6 shadow-[0_30px_120px_rgba(0,0,0,0.55)] backdrop-blur-xl sm:p-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl">
                <p className="text-sm uppercase tracking-[0.3em] text-cyan-300/80">
                  7-Day Character Tierboard
                </p>
                <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-5xl">
                  최근 7일 랭크 기준 캐릭터 티어표
                </h1>
                <p className="mt-4 text-sm leading-7 text-zinc-300 sm:text-base">
                  최근 수집된 랭크 데이터를 기준으로 RP 획득량, 픽률, 승률, Top3 비율,
                  평균 순위, 딜량, 평균 TK, 플레이어킬을 집계했습니다.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:min-w-[520px]">
                <div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-zinc-500">Window</p>
                  <div className="mt-3">
                    <Select
                      value={windowFilter}
                      onValueChange={(value) => setWindowFilter(value as WindowFilter)}
                    >
                      <SelectTrigger className="h-10 w-full border-white/10 bg-zinc-950/60 text-zinc-100">
                        <SelectValue placeholder="Select window" />
                      </SelectTrigger>
                      <SelectContent className="border-white/10 bg-zinc-950 text-zinc-100">
                        <SelectItem value="1">1주 전</SelectItem>
                        <SelectItem value="2">2주 전</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-zinc-400">
                    {data ? `${data.windowStart} ~ ${data.windowEnd}` : "-"}
                  </p>
                </div>
                <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-5 py-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-cyan-200/70">Tier Filter</p>
                  <div className="mt-3">
                    <Select
                      value={rankTierFilter}
                      onValueChange={(value) => setRankTierFilter(value as RankTierFilter)}
                    >
                      <SelectTrigger className="h-10 w-full border-cyan-400/20 bg-zinc-950/60 text-cyan-100">
                        <SelectValue placeholder="Select rank tier" />
                      </SelectTrigger>
                      <SelectContent className="border-white/10 bg-zinc-950 text-zinc-100">
                        <SelectItem value="diamond">Diamond</SelectItem>
                        <SelectItem value="meteor">Meteor</SelectItem>
                        <SelectItem value="mithril">Mithril+</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-cyan-100/70">
                    {windowLabel} {filterLabel} 구간 통계
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-8 grid gap-4 lg:grid-cols-3">
              {topEntries.map((entry) => (
                <div
                  key={entry.characterNum}
                  className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/10 to-white/[0.03] p-5"
                >
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <CharacterAvatar
                        name={entry.characterName}
                        image={getCharacterImage(entry.characterName)}
                        weaponCode={getCharacterWeaponCode(entry.characterName)}
                        size="lg"
                      />
                      <span className="absolute -left-2 -top-2 rounded-full bg-zinc-950 px-2 py-1 text-xs font-bold text-zinc-200 ring-1 ring-white/10">
                        #{entry.rank}
                      </span>
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-white">{entry.characterName}</p>
                      <span
                        className={cn(
                          "mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-semibold",
                          tierStyles[entry.tier] ?? tierStyles.D
                        )}
                      >
                        {entry.tier} Tier
                      </span>
                    </div>
                  </div>

                  <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-2xl bg-black/25 p-3">
                      <p className="text-zinc-500">{filterLabel} RP 획득</p>
                      <p className="mt-1 font-semibold text-white">
                        {decimalFormatter.format(entry.rpGain)}
                      </p>
                    </div>
                    <div className="rounded-2xl bg-black/25 p-3">
                      <p className="text-zinc-500">승률</p>
                      <p className="mt-1 font-semibold text-white">
                        {percentFormatter.format(entry.winRate)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="mt-8 rounded-[28px] border border-white/10 bg-zinc-950/85 p-4 shadow-[0_24px_90px_rgba(0,0,0,0.45)] backdrop-blur-xl sm:p-6">
            {isLoading ? (
              <div className="flex min-h-72 items-center justify-center text-zinc-400">
                <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                티어표를 불러오는 중입니다.
              </div>
            ) : error ? (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-5 text-sm text-red-200">
                {error}
              </div>
            ) : !data || data.entries.length === 0 ? (
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-5 text-sm text-zinc-300">
                표시할 티어 데이터가 없습니다.
              </div>
            ) : (
              <>
                <div className="mb-4 flex items-center justify-between text-sm text-zinc-400">
                  <p>{filterLabel} 기준 티어표</p>
                  <p>{sortLabel}</p>
                </div>

                <div className="hidden overflow-hidden rounded-3xl border border-white/10 lg:block">
                  <div className="overflow-x-auto">
                    <table className="min-w-full table-fixed">
                      <thead className="bg-white/[0.03] text-left text-[11px] uppercase tracking-[0.12em] text-zinc-500">
                        <tr>
                          <th className="w-20 whitespace-nowrap px-3 py-4">순위<SortButtons column="rank" /></th>
                          <th className="w-56 whitespace-nowrap px-3 py-4">이름<SortButtons column="characterName" /></th>
                          <th className="w-20 whitespace-nowrap px-3 py-4">티어<SortButtons column="tier" /></th>
                          <th className="w-24 whitespace-nowrap px-3 py-4">RP 획득<SortButtons column="rpGain" /></th>
                          <th className="w-20 whitespace-nowrap px-3 py-4">픽률<SortButtons column="pickRate" /></th>
                          <th className="w-20 whitespace-nowrap px-3 py-4">승률<SortButtons column="winRate" /></th>
                          <th className="w-20 whitespace-nowrap px-3 py-4">Top3<SortButtons column="top3Rate" /></th>
                          <th className="w-24 whitespace-nowrap px-3 py-4">평균순위<SortButtons column="averageRank" /></th>
                          <th className="w-24 whitespace-nowrap px-3 py-4">딜량<SortButtons column="averageDamage" /></th>
                          <th className="w-24 whitespace-nowrap px-3 py-4">평균 TK<SortButtons column="averageTakenDamage" /></th>
                          <th className="w-24 whitespace-nowrap px-3 py-4">플레이어킬<SortButtons column="averagePlayerKill" /></th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedEntries.map((entry) => (
                          <tr
                            key={entry.characterNum}
                            className="border-t border-white/5 text-sm text-zinc-100 transition-colors hover:bg-white/[0.035]"
                          >
                            <td className="px-4 py-4 font-semibold text-zinc-400">
                              {entry.rank}
                            </td>
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-3">
                                <CharacterAvatar
                                  name={entry.characterName}
                                  image={getCharacterImage(entry.characterName)}
                                  weaponCode={getCharacterWeaponCode(entry.characterName)}
                                  size="md"
                                />
                                <div>
                                  <p className="font-semibold text-white">{entry.characterName}</p>
                                  <p className="text-xs text-zinc-500">#{entry.characterNum}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <span
                                className={cn(
                                  "inline-flex rounded-full px-2.5 py-1 text-xs font-semibold",
                                  tierStyles[entry.tier] ?? tierStyles.D
                                )}
                              >
                                {entry.tier}
                              </span>
                            </td>
                            <td className="px-4 py-4 font-semibold text-cyan-300">
                              {decimalFormatter.format(entry.rpGain)}
                            </td>
                            <td className="px-4 py-4">{percentFormatter.format(entry.pickRate)}%</td>
                            <td className="px-4 py-4">{percentFormatter.format(entry.winRate)}%</td>
                            <td className="px-4 py-4">{percentFormatter.format(entry.top3Rate)}%</td>
                            <td className="px-4 py-4">#{decimalFormatter.format(entry.averageRank)}</td>
                            <td className="px-4 py-4">{numberFormatter.format(entry.averageDamage)}</td>
                            <td className="px-4 py-4">{numberFormatter.format(entry.averageTakenDamage)}</td>
                            <td className="px-4 py-4">{decimalFormatter.format(entry.averagePlayerKill)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="grid gap-3 lg:hidden">
                  {sortedEntries.map((entry) => (
                    <article
                      key={entry.characterNum}
                      className="rounded-3xl border border-white/10 bg-white/[0.03] p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <CharacterAvatar
                            name={entry.characterName}
                            image={getCharacterImage(entry.characterName)}
                            weaponCode={getCharacterWeaponCode(entry.characterName)}
                            size="lg"
                          />
                          <div>
                            <p className="text-sm text-zinc-500">#{entry.rank}</p>
                            <p className="text-lg font-semibold text-white">{entry.characterName}</p>
                          </div>
                        </div>
                        <span
                          className={cn(
                            "inline-flex rounded-full px-2.5 py-1 text-xs font-semibold",
                            tierStyles[entry.tier] ?? tierStyles.D
                          )}
                        >
                          {entry.tier}
                        </span>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">{filterLabel} RP 획득</p>
                          <p className="mt-1 font-semibold text-white">{decimalFormatter.format(entry.rpGain)}</p>
                        </div>
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">픽률</p>
                          <p className="mt-1 font-semibold text-white">{percentFormatter.format(entry.pickRate)}%</p>
                        </div>
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">승률</p>
                          <p className="mt-1 font-semibold text-white">{percentFormatter.format(entry.winRate)}%</p>
                        </div>
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">Top3</p>
                          <p className="mt-1 font-semibold text-white">{percentFormatter.format(entry.top3Rate)}%</p>
                        </div>
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">평균순위</p>
                          <p className="mt-1 font-semibold text-white">#{decimalFormatter.format(entry.averageRank)}</p>
                        </div>
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">딜량</p>
                          <p className="mt-1 font-semibold text-white">{numberFormatter.format(entry.averageDamage)}</p>
                        </div>
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">평균 TK</p>
                          <p className="mt-1 font-semibold text-white">{numberFormatter.format(entry.averageTakenDamage)}</p>
                        </div>
                        <div className="rounded-2xl bg-black/25 p-3">
                          <p className="text-zinc-500">플레이어킬</p>
                          <p className="mt-1 font-semibold text-white">{decimalFormatter.format(entry.averagePlayerKill)}</p>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}
