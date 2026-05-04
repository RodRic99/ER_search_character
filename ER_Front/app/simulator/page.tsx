"use client"

import { useState } from "react"
import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ChevronDown, ChevronUp, HelpCircle, X } from "lucide-react"
import { characters, getCharacterImage, type Character } from "@/lib/characters"
import { cn } from "@/lib/utils"

type TeamResult = {
  id: number
  members: string[]
  score: number
  grade: string
}

type TeamMember = {
  id: number | null
  name: string
  image: string
}

const sampleResults: TeamResult[] = [
  { id: 1, members: ["DebiMarlene", "Johann", "Chloe"], score: 8.0, grade: "A" },
  { id: 2, members: ["DebiMarlene", "Tsubame", "Hyunwoo"], score: 7.9, grade: "A" },
  { id: 3, members: ["DebiMarlene", "Shoichi", "Yuki"], score: 7.8, grade: "A" },
  { id: 4, members: ["DebiMarlene", "Rio", "Zahir"], score: 7.6, grade: "A" },
]

export default function SimulatorPage() {
  const [showHelp, setShowHelp] = useState(true)
  const [tier, setTier] = useState("top4")
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([
    { id: 1, name: "DebiMarlene", image: getCharacterImage("DebiMarlene") },
    { id: 2, name: "Johann", image: getCharacterImage("Johann") },
    { id: null, name: "", image: "" },
  ])
  const [searchInputs, setSearchInputs] = useState(["", "", ""])
  const [expandedResult, setExpandedResult] = useState<number | null>(null)
  const [characterSearch, setCharacterSearch] = useState("")
  const [selectedCharacters, setSelectedCharacters] = useState<number[]>([])

  const filteredCharacters = characters.filter((character) => {
    if (!characterSearch) return true
    return character.name.toLowerCase().includes(characterSearch.toLowerCase())
  })

  const handleCharacterSelect = (characterId: number) => {
    if (selectedCharacters.includes(characterId)) {
      setSelectedCharacters(selectedCharacters.filter((id) => id !== characterId))
      return
    }

    setSelectedCharacters([...selectedCharacters, characterId])
  }

  const handleRemoveMember = (index: number) => {
    const nextMembers = [...teamMembers]
    nextMembers[index] = { id: null, name: "", image: "" }
    setTeamMembers(nextMembers)
  }

  const handleSearchChange = (index: number, value: string) => {
    const nextInputs = [...searchInputs]
    nextInputs[index] = value
    setSearchInputs(nextInputs)

    const matchedCharacter = characters.find(
      (character) => character.name.toLowerCase() === value.trim().toLowerCase()
    )

    if (!matchedCharacter) return

    const nextMembers = [...teamMembers]
    nextMembers[index] = {
      id: matchedCharacter.id,
      name: matchedCharacter.name,
      image: matchedCharacter.image,
    }
    setTeamMembers(nextMembers)
  }

  const filledMemberCount = teamMembers.filter((member) => member.id !== null).length

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold text-foreground">Simulator</h1>

        <div className="mt-6 rounded-lg border border-primary/50 bg-primary/5 p-4">
          <div className="flex items-start justify-between gap-4">
            <div className={cn("space-y-1 text-sm text-muted-foreground", !showHelp && "hidden")}>
              <p>Pick characters from the list and use the three team slots to preview combinations.</p>
              <p>Character portraits are now loaded directly from the files you placed in `public/character_img`.</p>
              <p>Type an exact character name in a slot to fill that card with the matching portrait.</p>
            </div>
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="shrink-0 text-sm text-muted-foreground hover:text-foreground"
            >
              Help {showHelp ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-border bg-card p-4">
          <h2 className="text-lg font-bold text-foreground">Character Select</h2>

          <div className="mt-4">
            <Input
              placeholder="Search characters"
              value={characterSearch}
              onChange={(event) => setCharacterSearch(event.target.value)}
              className="w-full"
            />
          </div>

          <div className="mt-4 max-h-80 overflow-y-auto">
            <div className="grid grid-cols-5 gap-3 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10">
              {filteredCharacters.map((character) => {
                const isSelected = selectedCharacters.includes(character.id)
                return (
                  <button
                    key={character.id}
                    onClick={() => handleCharacterSelect(character.id)}
                    className={cn(
                      "flex flex-col items-center gap-1 rounded-lg p-2 transition-colors",
                      isSelected ? "bg-primary/20 ring-2 ring-primary" : "hover:bg-secondary"
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

          {selectedCharacters.length > 0 && (
            <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
              <span>{selectedCharacters.length} selected</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedCharacters([])}
                className="h-6 text-xs"
              >
                Clear
              </Button>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center gap-3">
          <span className="text-sm text-muted-foreground">Tier range:</span>
          <Select value={tier} onValueChange={setTier}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="top1">Top 1%</SelectItem>
              <SelectItem value="top4">Top 4%</SelectItem>
              <SelectItem value="top10">Top 10%</SelectItem>
              <SelectItem value="top25">Top 25%</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {[0, 1, 2].map((index) => {
            const member = teamMembers[index]
            const hasMember = member.id !== null

            return (
              <div key={index} className="rounded-lg border border-border bg-card p-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-foreground">Member {index + 1}</span>
                  {index === 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 border-primary/50 text-xs text-primary"
                    >
                      Auto fill ON
                    </Button>
                  )}
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
                        Enter an exact character name
                      </span>
                    </>
                  )}
                </div>

                <div className="relative mt-4">
                  <Input
                    placeholder="Type character name"
                    value={searchInputs[index]}
                    onChange={(event) => handleSearchChange(index, event.target.value)}
                    className="pr-8"
                  />
                  {hasMember && (
                    <button
                      onClick={() => handleRemoveMember(index)}
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

        <div className="mt-10">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">Recommended Teams</h2>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              Build with {filledMemberCount} members
            </Button>
          </div>

          <div className="mt-4 space-y-2">
            {sampleResults.map((result) => (
              <div key={result.id} className="rounded-lg border border-border bg-card">
                <div className="flex items-center justify-between p-4">
                  <div className="flex flex-wrap items-center gap-6">
                    {result.members.map((memberName, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <div className="h-10 w-10 overflow-hidden rounded-full bg-secondary">
                          <img
                            src={getCharacterImage(memberName)}
                            alt={memberName}
                            className="h-full w-full object-cover"
                          />
                        </div>
                        <span className="text-sm text-foreground">{memberName}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center gap-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setExpandedResult(expandedResult === result.id ? null : result.id)}
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
                          result.grade === "A" && "text-primary",
                          result.grade === "B" && "text-green-500",
                          result.grade === "C" && "text-yellow-500"
                        )}
                      >
                        {result.grade}
                      </span>
                      <span className="text-xs text-muted-foreground">Score {result.score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>

                {expandedResult === result.id && (
                  <div className="border-t border-border p-4">
                    <p className="text-sm text-muted-foreground">
                      This area can later show synergy details and recommendation reasons.
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2026 StatTracker. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
