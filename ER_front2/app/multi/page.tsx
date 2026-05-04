"use client"

import { useState } from "react"
import { Navigation } from "@/components/navigation"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Plus, Search, X } from "lucide-react"

export default function MultiSearchPage() {
  const [usernames, setUsernames] = useState<string[]>(["", "", "", "", ""])

  const updateUsername = (index: number, value: string) => {
    const next = [...usernames]
    next[index] = value
    setUsernames(next)
  }

  const clearUsername = (index: number) => {
    updateUsername(index, "")
  }

  const addUser = () => {
    if (usernames.length < 10) {
      setUsernames([...usernames, ""])
    }
  }

  const removeUser = (index: number) => {
    if (usernames.length > 1) {
      setUsernames(usernames.filter((_, currentIndex) => currentIndex !== index))
    }
  }

  const filledCount = usernames.filter((username) => username.trim() !== "").length

  const handleSearch = () => {
    const filled = usernames.filter((username) => username.trim() !== "")
    if (filled.length > 0) {
      console.log("multi search", filled)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-2xl font-bold text-foreground">Multi search</h1>
        <p className="mt-2 text-muted-foreground">
          Search several player names at once. You can add up to 10 entries.
        </p>

        <div className="mt-8 rounded-lg border border-border bg-card p-6">
          <div className="space-y-3">
            {usernames.map((username, index) => (
              <div key={index} className="flex items-center gap-2">
                <span className="w-8 text-sm text-muted-foreground">{index + 1}.</span>
                <div className="relative flex-1">
                  <Input
                    placeholder={`Player ${index + 1}`}
                    value={username}
                    onChange={(e) => updateUsername(index, e.target.value)}
                    className="pr-10"
                  />
                  {username && (
                    <button
                      type="button"
                      onClick={() => clearUsername(index)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
                {usernames.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeUser(index)}
                    className="h-9 w-9 text-muted-foreground hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>

          {usernames.length < 10 && (
            <Button variant="outline" onClick={addUser} className="mt-4 w-full">
              <Plus className="mr-2 h-4 w-4" />
              Add player
            </Button>
          )}

          <Button
            onClick={handleSearch}
            disabled={filledCount === 0}
            className="mt-6 w-full"
          >
            <Search className="mr-2 h-4 w-4" />
            {filledCount > 0
              ? `Search ${filledCount} player${filledCount > 1 ? "s" : ""}`
              : "Enter a player name"}
          </Button>
        </div>
      </main>
    </div>
  )
}
