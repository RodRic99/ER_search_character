"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, User, X, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"

// 샘플 검색 결과 데이터
const sampleResults = [
  {
    id: 1,
    characters: [
      { name: "데비 마를렌", image: "/placeholder.svg?height=40&width=40" },
      { name: "헤이즈", image: "/placeholder.svg?height=40&width=40" },
      { name: "현우 - 글러브", image: "/placeholder.svg?height=40&width=40" },
    ],
    grade: "B",
    score: 5.5,
  },
  {
    id: 2,
    characters: [
      { name: "데비 마를렌", image: "/placeholder.svg?height=40&width=40" },
      { name: "헤이즈", image: "/placeholder.svg?height=40&width=40" },
      { name: "아야 - 돌격소총", image: "/placeholder.svg?height=40&width=40" },
    ],
    grade: "A",
    score: 7.2,
  },
  {
    id: 3,
    characters: [
      { name: "데비 마를렌", image: "/placeholder.svg?height=40&width=40" },
      { name: "헤이즈", image: "/placeholder.svg?height=40&width=40" },
      { name: "나딘 - 석궁", image: "/placeholder.svg?height=40&width=40" },
    ],
    grade: "A",
    score: 8.0,
  },
]

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

export function SearchForm() {
  const [usernames, setUsernames] = useState(["", "", ""])
  const [showResults, setShowResults] = useState(false)
  const [expandedResult, setExpandedResult] = useState<number | null>(null)

  const handleUsernameChange = (index: number, value: string) => {
    const newUsernames = [...usernames]
    newUsernames[index] = value
    setUsernames(newUsernames)
  }

  const handleClear = (index: number) => {
    const newUsernames = [...usernames]
    newUsernames[index] = ""
    setUsernames(newUsernames)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const filledUsernames = usernames.filter((u) => u.trim() !== "")
    if (filledUsernames.length > 0) {
      setShowResults(true)
    }
  }

  const filledCount = usernames.filter((u) => u.trim() !== "").length

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit}>
        <div className="rounded-xl border border-border bg-card p-6 shadow-lg">
          <div className="mb-6 text-center">
            <h2 className="text-lg font-semibold text-foreground">
              유저 검색
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              검색할 유저의 닉네임을 입력하세요
            </p>
          </div>

          {/* 가로 배치된 입력 필드 */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {usernames.map((username, index) => (
              <div key={index} className="group relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <User className="h-4 w-4 text-muted-foreground" />
                </div>
                <Input
                  type="text"
                  placeholder={`유저 ${index + 1}`}
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
            ))}
          </div>

          <Button
            type="submit"
            size="lg"
            className="mt-5 w-full gap-2"
            disabled={filledCount === 0}
          >
            <Search className="h-4 w-4" />
            {filledCount > 0 ? `${filledCount}명 검색하기` : "검색"}
          </Button>
        </div>
      </form>

      {/* 검색 결과 */}
      {showResults && (
        <div className="mt-6 rounded-xl border border-border bg-card p-4 shadow-lg">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">조합 추천 결과</h3>
            <span className="rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
              {filledCount}인 조합 계산
            </span>
          </div>

          <div className="flex flex-col gap-2">
            {sampleResults.map((result) => (
              <div
                key={result.id}
                className="rounded-lg border border-border bg-secondary/50 transition-colors hover:bg-secondary"
              >
                {/* 결과 행 */}
                <div className="flex items-center justify-between p-3">
                  {/* 캐릭터 목록 (가로 배치) */}
                  <div className="flex flex-1 items-center gap-6">
                    {result.characters.map((char, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <div className="h-9 w-9 overflow-hidden rounded-full bg-muted">
                          <img
                            src={char.image}
                            alt={char.name}
                            className="h-full w-full object-cover"
                          />
                        </div>
                        <span className="text-sm font-medium text-foreground">
                          {char.name}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* 상세보기 버튼 */}
                  <button
                    onClick={() =>
                      setExpandedResult(
                        expandedResult === result.id ? null : result.id
                      )
                    }
                    className="flex items-center gap-1 rounded-md bg-muted px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground"
                  >
                    상세보기
                    {expandedResult === result.id ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </button>

                  {/* 점수 및 등급 */}
                  <div className="ml-4 flex flex-col items-end">
                    <span
                      className={cn(
                        "text-2xl font-bold",
                        getGradeColor(result.grade)
                      )}
                    >
                      {result.grade}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      점수 {result.score.toFixed(1)}
                    </span>
                  </div>
                </div>

                {/* 상세보기 확장 영역 */}
                {expandedResult === result.id && (
                  <div className="border-t border-border bg-background/50 p-4">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">평균 순위</span>
                        <p className="font-medium text-foreground">2.4위</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">승률</span>
                        <p className="font-medium text-foreground">32.5%</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">표본 수</span>
                        <p className="font-medium text-foreground">1,234게임</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
