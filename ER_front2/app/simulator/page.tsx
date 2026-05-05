"use client"

import { useState } from "react"
import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import {
  ArrowDownAZ,
  ArrowDownUp,
  ArrowDownWideNarrow,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Loader2,
  X,
} from "lucide-react"
import { characters, getCharacterImage, getCharacterWeaponCode } from "@/lib/characters"
import { cn } from "@/lib/utils"
import { CharacterAvatar } from "@/components/character-avatar"
import { CharacterSynergyStrip } from "../../components/character-synergy-strip"

interface SimulatorResult {
  id: number
  members: string[]
  weaponCodes?: number[]
  score: number
  grade: string
  rawPredictedAvgGetmmr?: number | null
  playerNames?: string[]
  characterPools?: number[][]
  synergyValues?: Array<number | null | undefined>
  synergyRawValues?: Array<number | null | undefined>
  pairPositionLabels?: Array<string | null | undefined>
  positionSummary?: string
  positionMainCombo?: string
  positionSubCombo?: string
  samePositionAverageGetmmr?: number | null
  samePositionAverageGetmmrScore?: number | null
  samePositionSampleCount?: number | null
  samePositionAverageDamage?: number | null
  samePositionAverageHealAmount?: number | null
}

interface TeamMember {
  id: number | null
  name: string
  image: string
  weaponCode?: number
}

type SortOption = "name" | "id-asc" | "id-desc"

interface Most3PlayerItem {
  playerName: string
  userId: string
  most3Characters: string[]
  most3CharacterNums?: number[]
}

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080"

const calculateGrade = (score: number): string => {
  if (score >= 90) return "S"
  if (score >= 75) return "A"
  if (score >= 60) return "B"
  return "C"
}

// localeCompare는 서버와 브라우저 환경에 따라 결과가 달라질 수 있어서
// hydration mismatch를 피하려고 고정된 문자열 비교를 사용한다.
const compareKoreanNames = (left: string, right: string) => {
  const normalizedLeft = left.normalize("NFC")
  const normalizedRight = right.normalize("NFC")

  if (normalizedLeft < normalizedRight) return -1
  if (normalizedLeft > normalizedRight) return 1
  return 0
}

const HANGUL_INITIALS = [
  "ㄱ",
  "ㄲ",
  "ㄴ",
  "ㄷ",
  "ㄸ",
  "ㄹ",
  "ㅁ",
  "ㅂ",
  "ㅃ",
  "ㅅ",
  "ㅆ",
  "ㅇ",
  "ㅈ",
  "ㅉ",
  "ㅊ",
  "ㅋ",
  "ㅌ",
  "ㅍ",
  "ㅎ",
]

const getKoreanInitials = (value: string) =>
  value
    .normalize("NFC")
    .split("")
    .map((character) => {
      const code = character.charCodeAt(0)
      if (code >= 0xac00 && code <= 0xd7a3) {
        const initialIndex = Math.floor((code - 0xac00) / 588)
        return HANGUL_INITIALS[initialIndex] ?? character
      }
      return character
    })
    .join("")

const normalizeSearchText = (value: string) =>
  value.normalize("NFC").toLowerCase().replace(/\s+/g, "")

const matchesCharacterSearch = (characterName: string, searchValue: string) => {
  const normalizedSearch = normalizeSearchText(searchValue)
  if (!normalizedSearch) return true

  const normalizedName = normalizeSearchText(characterName)
  if (normalizedName.includes(normalizedSearch)) {
    return true
  }

  const initials = normalizeSearchText(getKoreanInitials(characterName))
  return initials.includes(normalizedSearch)
}

export default function SimulatorPage() {
  const [showHelp, setShowHelp] = useState(true)
  const [sortOption, setSortOption] = useState<SortOption>("name")
  const [searchInputs, setSearchInputs] = useState(["", "", ""])
  const [expandedResult, setExpandedResult] = useState<number | null>(null)
  const [characterSearch, setCharacterSearch] = useState("")
  const [selectedCharacters, setSelectedCharacters] = useState<number[]>([])
  const [simulatorResults, setSimulatorResults] = useState<SimulatorResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 실제 선택 상태는 selectedCharacters에만 보관하고,
  // 각 슬롯 카드는 렌더링할 때마다 파생해서 사용한다.
  const teamMembers: TeamMember[] = [0, 1, 2].map((index) => {
    const charId = selectedCharacters[index]
    if (charId !== undefined) {
      const character = characters.find((item) => item.id === charId)
      if (character) {
        return {
          id: character.id,
          name: character.name,
          image: character.image,
          weaponCode: character.weaponCode,
        }
      }
    }
    return { id: null, name: "", image: "" }
  })

  // 원본 캐릭터 목록은 유지하고 검색/정렬은 복사본에서만 수행한다.
  const filteredCharacters = [...characters]
    .filter((character) => {
      return matchesCharacterSearch(character.name, characterSearch)
    })
    .sort((left, right) => {
      if (sortOption === "id-asc") return left.id - right.id
      if (sortOption === "id-desc") return right.id - left.id
      return compareKoreanNames(left.name, right.name)
    })

  const sortLabel =
    sortOption === "name"
      ? "가나다 정렬"
      : sortOption === "id-asc"
        ? "ID 오름차순"
        : "ID 내림차순"

  const activeSlotCount = [0, 1, 2].filter(
    (index) => searchInputs[index].trim() !== "" || teamMembers[index].id !== null
  ).length

  const calculateLabel =
    activeSlotCount >= 3 ? "Calculate Top 5" : activeSlotCount >= 2 ? "Calculate Top 10" : "Need 2 Slots"

  const handleCharacterSelect = (charId: number) => {
    // 같은 카드를 다시 누르면 선택 해제된다.
    if (selectedCharacters.includes(charId)) {
      setSelectedCharacters(selectedCharacters.filter((id) => id !== charId))
      return
    }

    // 시뮬레이터는 최대 3슬롯만 사용하므로 선택도 3개까지 제한한다.
    if (selectedCharacters.length < 3) {
      setSelectedCharacters([...selectedCharacters, charId])
    }
  }

  const handleSearchChange = (index: number, value: string) => {
    const nextInputs = [...searchInputs]
    nextInputs[index] = value
    setSearchInputs(nextInputs)
  }

  const buildCharacterPools = async () => {
    const slotPools: Array<number[] | null> = [null, null, null]
    const nicknameSlots = searchInputs
      .map((value, index) => ({ playerName: value.trim(), index }))
      .filter((slot) => slot.playerName.length > 0)

    if (nicknameSlots.length > 0) {
      const response = await fetch(`${apiBaseUrl}/api/player-stats/most3`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          playerNames: nicknameSlots.map((slot) => slot.playerName),
        }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()
      const players: Most3PlayerItem[] = Array.isArray(data?.players) ? data.players : []

      nicknameSlots.forEach((slot, index) => {
        const player = players[index]
        const most3CharacterNums = Array.isArray(player?.most3CharacterNums)
          ? player.most3CharacterNums.filter((characterNum) => Number.isInteger(characterNum))
          : []

        if (most3CharacterNums.length > 0) {
          slotPools[slot.index] = most3CharacterNums
        }
      })
    }

    // 닉네임이 없는 슬롯만 직접 선택한 실험체를 단일 후보 풀로 사용한다.
    teamMembers.forEach((member, index) => {
      if (!slotPools[index] && member.id !== null) {
        slotPools[index] = [member.id]
      }
    })

    return slotPools.filter((pool): pool is number[] => Array.isArray(pool) && pool.length > 0)
  }

  const handleCalculate = async () => {
    const requestPlayerNames = searchInputs
      .map((value) => value.trim())
      .filter((value) => value.length > 0)

    setIsLoading(true)
    setError(null)

    try {
      // 프론트는 슬롯별 후보 풀만 구성하고,
      // 실제 시나리오 생성과 Top N 필터링은 서버의 사전 계산 데이터셋 조회에 맡긴다.
      const characterPools = await buildCharacterPools()

      if (characterPools.length < 2) {
        setSimulatorResults([])
        setError("At least 2 simulator slots are required.")
        return
      }

      const response = await fetch(`${apiBaseUrl}/api/player-stats/simulate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          characterPools,
        }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()
      const resolvedPools = Array.isArray(data?.characterPools) ? data.characterPools : characterPools
      const formattedResults: SimulatorResult[] = Array.isArray(data?.recommendedCombinations)
        ? data.recommendedCombinations.map((item: any, index: number) => ({
            id: index + 1,
            members: Array.isArray(item.characterNames) ? item.characterNames : [],
            weaponCodes: Array.isArray(item.weaponCodes) ? item.weaponCodes : [],
            score: item.overallScore ?? item.predictedAvgGetmmrScore ?? item.predictedAvgGetmmr ?? 0,
            grade: calculateGrade(item.overallScore ?? item.predictedAvgGetmmrScore ?? item.predictedAvgGetmmr ?? 0),
            rawPredictedAvgGetmmr: item.predictedAvgGetmmr ?? null,
            playerNames: requestPlayerNames,
            characterPools: resolvedPools,
            synergyValues: [
              item.characterSynergy1Score,
              item.characterSynergy2Score,
              item.characterSynergy3Score,
            ],
            synergyRawValues: [
              item.characterSynergy1,
              item.characterSynergy2,
              item.characterSynergy3,
            ],
            pairPositionLabels: item.pairPositionLabels,
            positionSummary: item.positionSummary ?? undefined,
            positionMainCombo: item.positionMainCombo ?? undefined,
            positionSubCombo: item.positionSubCombo ?? undefined,
            samePositionAverageGetmmr: item.samePositionAverageGetmmr ?? null,
            samePositionAverageGetmmrScore: item.samePositionAverageGetmmrScore ?? null,
            samePositionSampleCount: item.samePositionSampleCount ?? null,
            samePositionAverageDamage: item.samePositionAverageDamage ?? null,
            samePositionAverageHealAmount: item.samePositionAverageHealAmount ?? null,
          }))
        : []

      setSimulatorResults(formattedResults)

      if (formattedResults.length === 0) {
        setError(
          resolvedPools.length === 2
            ? "No matching combinations were found for this 2-slot fixed lookup."
            : "No matching combinations were found for this 3-slot lookup."
        )
      }
    } catch (err) {
      setSimulatorResults([])
      setError(err instanceof Error ? err.message : "Request failed.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold text-foreground">Team simulator</h1>

        <div className="mt-6 rounded-lg border border-primary/50 bg-primary/5 p-4">
          <div className="flex items-start justify-between gap-4">
            {showHelp && (
              <div className="space-y-1 text-sm text-muted-foreground">
                <p>Select up to three characters to preview likely team combinations.</p>
                <p>
                  Nickname slots use the player&apos;s most 3 characters, while direct
                  character picks stay fixed as single-character pools.
                </p>
                <p>
                  The simulator queries the precomputed combination dataset and returns
                  Top 10 for 2 slots or Top 5 for 3 slots.
                </p>
              </div>
            )}
            <button
              type="button"
              onClick={() => setShowHelp(!showHelp)}
              className="shrink-0 text-sm text-muted-foreground hover:text-foreground"
            >
              {showHelp ? "Hide help" : "Show help"}
            </button>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-bold text-foreground">Character selection</h2>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  <ArrowDownUp className="h-4 w-4" />
                  {sortLabel}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setSortOption("name")}>
                  <ArrowDownAZ className="h-4 w-4" />
                  가나다 정렬
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortOption("id-asc")}>
                  <ArrowDownWideNarrow className="h-4 w-4" />
                  ID 오름차순
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortOption("id-desc")}>
                  <ArrowDownWideNarrow className="h-4 w-4 rotate-180" />
                  ID 내림차순
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="mt-4">
            <Input
              placeholder="Search characters"
              value={characterSearch}
              onChange={(e) => setCharacterSearch(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="mt-4 max-h-80 overflow-y-auto">
            <div className="grid grid-cols-4 gap-3 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8">
              {filteredCharacters.map((character) => {
                const isSelected = selectedCharacters.includes(character.id)
                const isDisabled = !isSelected && selectedCharacters.length >= 3

                return (
                  <button
                    key={character.id}
                    type="button"
                    onClick={() => handleCharacterSelect(character.id)}
                    disabled={isDisabled}
                    className={cn(
                      "flex flex-col items-center gap-1 rounded-lg p-2 transition-colors",
                      isSelected
                        ? "bg-primary/20 ring-2 ring-primary"
                        : isDisabled
                          ? "cursor-not-allowed opacity-40"
                          : "hover:bg-secondary"
                    )}
                  >
                    <div className="relative h-12 w-12 overflow-hidden rounded-full bg-secondary">
                      <img
                        src={character.image}
                        alt={character.name}
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <span className="text-center text-xs leading-tight text-foreground">
                      {character.name}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
            <span>{selectedCharacters.length}/3 selected</span>
            {selectedCharacters.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedCharacters([])}
                className="h-6 text-xs"
              >
                Clear
              </Button>
            )}
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {[0, 1, 2].map((index) => {
            const member = teamMembers[index]
            const hasMember = member.id !== null

            return (
              <div key={index} className="rounded-lg border border-border bg-card p-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-foreground">Slot {index + 1}</span>
                </div>

                <div className="mt-4 flex flex-col items-center">
                  {hasMember ? (
                    <>
                      <div className="relative h-16 w-16 overflow-hidden rounded-full bg-secondary">
                        <img
                          src={member.image}
                          alt={member.name}
                          className="h-full w-full object-cover"
                        />
                      </div>
                      <span className="mt-2 text-sm text-foreground">{member.name}</span>
                    </>
                  ) : (
                    <>
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
                        <HelpCircle className="h-8 w-8 text-muted-foreground" />
                      </div>
                      <span className="mt-2 text-sm text-muted-foreground">
                        Pick a character above
                      </span>
                    </>
                  )}
                </div>

                <div className="relative mt-4">
                  <Input
                    placeholder={`Player nickname ${index + 1}`}
                    value={searchInputs[index]}
                    onChange={(e) => handleSearchChange(index, e.target.value)}
                    className="pr-8"
                  />
                  {searchInputs[index] && (
                    <button
                      type="button"
                      onClick={() => handleSearchChange(index, "")}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>

              </div>
            )
          })}
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-destructive bg-destructive/10 p-4 text-center">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <div className="mt-10">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">Simulation results</h2>
            <Button
              onClick={handleCalculate}
              disabled={activeSlotCount < 2 || isLoading}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isLoading ? "Calculating..." : calculateLabel}
            </Button>
          </div>

          <div className="mt-4 space-y-2">
            {simulatorResults.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border bg-card p-8 text-center text-muted-foreground">
                Select at least two slots and run the simulator to see results.
              </div>
            ) : (
              simulatorResults.map((result) => (
                <div
                  key={result.id}
                  className="rounded-lg border border-border bg-card"
                >
                  <div className="flex items-center justify-between gap-4 p-4">
                    <div className="flex flex-1 flex-wrap items-center gap-6">
                      {result.members.map((memberName, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <CharacterAvatar
                            name={memberName}
                            image={getCharacterImage(memberName)}
                            weaponCode={result.weaponCodes?.[index] ?? getCharacterWeaponCode(memberName)}
                            size="sm"
                          />
                          <span className="text-sm text-foreground">{memberName}</span>
                        </div>
                      ))}
                    </div>

                    <div className="flex items-center gap-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setExpandedResult(
                            expandedResult === result.id ? null : result.id
                          )
                        }
                        className="gap-1"
                      >
                        Details
                        {expandedResult === result.id ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>

                      <div className="flex flex-col items-end">
                        <span
                          className={cn(
                            "text-3xl font-bold",
                            result.grade === "S" && "text-yellow-400",
                            result.grade === "A" && "text-primary",
                            result.grade === "B" && "text-green-500",
                            result.grade === "C" && "text-yellow-500"
                          )}
                        >
                          {result.grade}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          Score {result.score.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {expandedResult === result.id && (
                    <div className="border-t border-border p-4">
                      <CharacterSynergyStrip
                        characters={result.members.map((memberName, index) => ({
                          name: memberName,
                          image: getCharacterImage(memberName),
                          weaponCode:
                            result.weaponCodes?.[index] ?? getCharacterWeaponCode(memberName),
                        }))}
                        pairPositionLabels={result.pairPositionLabels}
                        values={result.synergyValues}
                        rawValues={result.synergyRawValues}
                        positionSummary={result.positionSummary}
                        positionMainCombo={result.positionMainCombo}
                        positionSubCombo={result.positionSubCombo}
                        samePositionAverageGetmmr={result.samePositionAverageGetmmr}
                        samePositionAverageGetmmrScore={result.samePositionAverageGetmmrScore}
                        samePositionSampleCount={result.samePositionSampleCount}
                        samePositionAverageDamage={result.samePositionAverageDamage}
                        samePositionAverageHealAmount={result.samePositionAverageHealAmount}
                        className="mb-4"
                      />

                      <div className="space-y-2 text-sm text-muted-foreground">
                        <p>
                          {result.characterPools?.length === 2
                            ? "2-slot fixed lookup / Top 10"
                            : "3-slot lookup / Top 5"}
                        </p>
                        {result.playerNames && result.playerNames.length > 0 && (
                          <p>Players: {result.playerNames.join(", ")}</p>
                        )}
                        {result.characterPools && result.characterPools.length > 0 && (
                          <p>
                            Pools:{" "}
                            {result.characterPools
                              .map((pool) => `[${pool.join(", ")}]`)
                              .join(" x ")}
                          </p>
                        )}
                        <p>Score formula: 0.6 x predicted score + 0.4 x position score</p>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2026 이리메타. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
