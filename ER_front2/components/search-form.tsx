"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ChevronDown, ChevronUp, Loader2, Search, User, X } from "lucide-react"
import { getCharacterImage } from "@/lib/characters"
import { cn } from "@/lib/utils"
import { CharacterAvatar } from "@/components/character-avatar"
import { CharacterSynergyStrip } from "@/components/character-synergy-strip"

interface SearchCharacter {
  name: string
  image: string
  weaponCode?: number
}

interface SearchResult {
  id: number
  characters: SearchCharacter[]
  grade: string
  score: number
  inputCombo?: string
  synergyValues?: Array<number | null | undefined>
  pairPositionLabels?: Array<string | null | undefined>
  positionSummary?: string
  samePositionAverageGetmmr?: number | null
  samePositionSampleCount?: number | null
}

interface Most3PlayerItem {
  playerName: string
  userId: string
  rankPoint?: number
  most3Characters: string[]
  most3CharacterNums?: number[]
  prediction?: Record<string, unknown>
}

interface RecommendedCombinationItem {
  characterNums?: number[]
  weaponCodes?: number[]
  characterNames?: string[]
  weaponNames?: string[]
  predictedAvgGetmmr?: number
  inputCombo?: string
  characterSynergy1?: number | null
  characterSynergy2?: number | null
  characterSynergy3?: number | null
  pairPositionLabels?: Array<string | null | undefined>
  samePositionAverageGetmmr?: number | null
  samePositionSampleCount?: number | null
  positionSummary?: string | null
}

interface PlayerMost3Response {
  players?: Most3PlayerItem[]
  recommendedCombinations?: RecommendedCombinationItem[]
  highestRankPointPlayerName?: string
  highestRankPoint?: number
  highestRankModelPredictionEnabled?: boolean
}

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080"

const MAIN_SEARCH_NICKNAME_STORAGE_KEY = "main-search:first-player-nickname"
const ENABLE_HIGHEST_RANK_MODEL_FLOW = false

const getGradeColor = (grade: string) => {
  switch (grade) {
    case "S":
      return "text-yellow-400"
    case "A":
      return "text-primary"
    case "B":
      return "text-green-400"
    case "C":
      return "text-muted-foreground"
    default:
      return "text-muted-foreground"
  }
}

const calculateGrade = (score: number): string => {
  if (score >= 9) return "S"
  if (score >= 7) return "A"
  if (score >= 5) return "B"
  return "C"
}

const selectHighestRankPointPlayer = (players: Most3PlayerItem[]) =>
  players.reduce<Most3PlayerItem | null>((highestPlayer, currentPlayer) => {
    if (typeof currentPlayer.rankPoint !== "number") {
      return highestPlayer
    }

    if (!highestPlayer || (highestPlayer.rankPoint ?? Number.NEGATIVE_INFINITY) < currentPlayer.rankPoint) {
      return currentPlayer
    }

    return highestPlayer
  }, null)

export function SearchForm() {
  // 입력칸 수가 고정되어 있으므로 배열 상태로 관리하면 렌더링과 수정이 단순해진다.
  const [usernames, setUsernames] = useState(["", "", ""])
  const [rememberFirstNickname, setRememberFirstNickname] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [expandedResult, setExpandedResult] = useState<number | null>(null)
  const [results, setResults] = useState<SearchResult[]>([])
  const [searchedPlayers, setSearchedPlayers] = useState<Most3PlayerItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const savedNickname = window.localStorage.getItem(MAIN_SEARCH_NICKNAME_STORAGE_KEY)
    if (!savedNickname) return

    setRememberFirstNickname(true)
    setUsernames((currentUsernames) => {
      const nextUsernames = [...currentUsernames]
      nextUsernames[0] = savedNickname
      return nextUsernames
    })
  }, [])

  useEffect(() => {
    if (rememberFirstNickname) {
      const trimmedNickname = usernames[0]?.trim() ?? ""
      if (trimmedNickname) {
        window.localStorage.setItem(MAIN_SEARCH_NICKNAME_STORAGE_KEY, trimmedNickname)
      } else {
        window.localStorage.removeItem(MAIN_SEARCH_NICKNAME_STORAGE_KEY)
      }
      return
    }

    window.localStorage.removeItem(MAIN_SEARCH_NICKNAME_STORAGE_KEY)
  }, [rememberFirstNickname, usernames])

  const handleUsernameChange = (index: number, value: string) => {
    const next = [...usernames]
    next[index] = value
    setUsernames(next)
  }

  const handleClear = (index: number) => {
    const next = [...usernames]
    next[index] = ""
    setUsernames(next)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const filledUsernames = usernames
      .map((username) => username.trim())
      .filter((username) => username !== "")

    if (filledUsernames.length === 0) return

    setIsLoading(true)
    setError(null)
    setShowResults(false)
    setExpandedResult(null)

    try {
      const response = await fetch(`${apiBaseUrl}/api/player-stats/most3`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          playerNames: filledUsernames,
        }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data: PlayerMost3Response = await response.json()
      const players = Array.isArray(data?.players) ? data.players : []
      const recommendedCombinations = Array.isArray(data?.recommendedCombinations)
        ? data.recommendedCombinations
        : []
      const highestRankPointPlayer = selectHighestRankPointPlayer(players)

      if (ENABLE_HIGHEST_RANK_MODEL_FLOW && highestRankPointPlayer) {
        console.info("Highest-rank model flow is prepared but disabled.", {
          playerName: highestRankPointPlayer.playerName,
          rankPoint: highestRankPointPlayer.rankPoint,
          most3CharacterNums: highestRankPointPlayer.most3CharacterNums,
        })
      }

      // 백엔드 조합 응답을 화면 카드 구조로 정규화해서 렌더링 책임을 단순하게 유지한다.
      const formattedResults: SearchResult[] = recommendedCombinations.map((item, index) => {
        const characterNames = Array.isArray(item.characterNames) ? item.characterNames : []
        const score = item.predictedAvgGetmmr ?? 0

        return {
          id: index + 1,
          characters: characterNames.map((name, characterIndex) => ({
            name,
            image: getCharacterImage(name),
            weaponCode: Array.isArray(item.weaponCodes) ? item.weaponCodes[characterIndex] : undefined,
          })),
          grade: calculateGrade(score),
          score,
          inputCombo: item.inputCombo,
          synergyValues: [
            item.characterSynergy1,
            item.characterSynergy2,
            item.characterSynergy3,
          ],
          pairPositionLabels: item.pairPositionLabels,
          positionSummary: item.positionSummary ?? undefined,
          samePositionAverageGetmmr: item.samePositionAverageGetmmr ?? null,
          samePositionSampleCount: item.samePositionSampleCount ?? null,
        }
      })

      setSearchedPlayers(players)
      setResults(formattedResults)
      setShowResults(true)

      if (formattedResults.length === 0) {
        setError("No recommended combinations were returned for the searched players.")
      }
    } catch (err) {
      setSearchedPlayers([])
      setResults([])
      setShowResults(true)
      setError(err instanceof Error ? err.message : "Request failed.")
    } finally {
      setIsLoading(false)
    }
  }

  const filledCount = usernames.filter((username) => username.trim() !== "").length

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit}>
        <div className="rounded-xl border border-border bg-card p-6 shadow-lg">
          <div className="mb-6 text-center">
            <h2 className="text-lg font-semibold text-foreground">Player search</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              3명의 닉네임을 입력해주세요
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {usernames.map((username, index) => (
              <div key={index}>
                <div className="group relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <User className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <Input
                    type="text"
                    placeholder={`Player ${index + 1}`}
                    value={username}
                    onChange={(e) => handleUsernameChange(index, e.target.value)}
                    className="h-11 bg-secondary pl-9 pr-9 text-foreground placeholder:text-muted-foreground focus-visible:ring-primary"
                  />
                  {username && (
                    <button
                      type="button"
                      onClick={() => handleClear(index)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>

                {index === 0 && (
                  <label className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={rememberFirstNickname}
                      onChange={(event) => setRememberFirstNickname(event.target.checked)}
                      className="h-4 w-4 rounded border-border"
                    />
                    <span>내 닉네임 기억하기</span>
                  </label>
                )}
              </div>
            ))}
          </div>

          <Button
            type="submit"
            size="lg"
            className="mt-5 w-full gap-2"
            disabled={filledCount === 0 || isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            {isLoading
              ? "Searching..."
              : filledCount > 0
                ? `Search ${filledCount} player${filledCount > 1 ? "s" : ""}`
                : "Search"}
          </Button>
        </div>
      </form>

      {error && (
        <div className="mt-6 rounded-xl border border-destructive bg-destructive/10 p-4 text-center">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {showResults && (
        <div className="mt-6 rounded-xl border border-border bg-card p-4 shadow-lg">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">Recommended teams</h3>
            <span className="rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
              {results.length} results
            </span>
          </div>

          {searchedPlayers.length > 0 && (
            <div className="mb-4 rounded-lg border border-border bg-background/60 p-3 text-sm text-muted-foreground">
              <p className="font-medium text-foreground">Searched players</p>
              <div className="mt-2 space-y-1">
                {searchedPlayers.map((player) => (
                  <p key={player.userId || player.playerName}>
                    {player.playerName}: {player.most3Characters.join(", ")}
                  </p>
                ))}
              </div>
            </div>
          )}

          {results.length === 0 ? (
            <p className="py-8 text-center text-muted-foreground">
              No results were returned.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {results.map((result) => (
                <div
                  key={result.id}
                  className="rounded-lg border border-border bg-secondary/50 transition-colors hover:bg-secondary"
                >
                  <div className="flex items-center justify-between gap-4 p-3">
                    <div className="flex flex-1 flex-wrap items-center gap-4">
                      {result.characters.map((character, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <CharacterAvatar
                            name={character.name}
                            image={character.image}
                            weaponCode={character.weaponCode}
                            size="sm"
                          />
                          <span className="text-sm font-medium text-foreground">
                            {character.name}
                          </span>
                        </div>
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        setExpandedResult(
                          expandedResult === result.id ? null : result.id
                        )
                      }
                      className="flex items-center gap-1 rounded-md bg-muted px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground"
                    >
                      Details
                      {expandedResult === result.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>

                    <div className="ml-4 flex flex-col items-end">
                      <span
                        className={cn("text-2xl font-bold", getGradeColor(result.grade))}
                      >
                        {result.grade}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Score {result.score.toFixed(1)}
                      </span>
                    </div>
                  </div>

                  <div className="px-3 pb-3">
                    <CharacterSynergyStrip
                      pairPositionLabels={result.pairPositionLabels}
                      values={result.synergyValues}
                      positionSummary={result.positionSummary}
                      samePositionAverageGetmmr={result.samePositionAverageGetmmr}
                      samePositionSampleCount={result.samePositionSampleCount}
                    />
                  </div>

                  {expandedResult === result.id && (
                    <div className="border-t border-border bg-background/50 p-4">
                      <div className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
                        <div>
                          <span className="text-muted-foreground">Input combo</span>
                          <p className="font-medium text-foreground">
                            {result.inputCombo ?? "-"}
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Predicted average MMR</span>
                          <p className="font-medium text-foreground">
                            {result.score.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
