"use client"

import { CharacterAvatar } from "@/components/character-avatar"

type SynergyCharacter = {
  name: string
  image: string
  weaponCode?: number
}

type CharacterSynergyStripProps = {
  characters: SynergyCharacter[]
  pairPositionLabels?: Array<string | null | undefined>
  values?: Array<number | null | undefined>
  rawValues?: Array<number | null | undefined>
  positionSummary?: string
  positionMainCombo?: string
  positionSubCombo?: string
  samePositionAverageGetmmr?: number | null
  samePositionAverageGetmmrScore?: number | null
  samePositionSampleCount?: number | null
  samePositionAverageDamage?: number | null
  samePositionAverageHealAmount?: number | null
  className?: string
}

const pairIndexes: Array<[number, number]> = [
  [0, 1],
  [0, 2],
  [1, 2],
]

const formatValue = (value?: number | null, fractionDigits = 1) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "N/A"
  }

  return value.toFixed(fractionDigits)
}

export function CharacterSynergyStrip({
  characters,
  pairPositionLabels = [],
  values = [],
  rawValues = [],
  positionSummary,
  positionMainCombo,
  positionSubCombo,
  samePositionAverageGetmmr,
  samePositionAverageGetmmrScore,
  samePositionSampleCount,
  samePositionAverageDamage,
  samePositionAverageHealAmount,
  className,
}: CharacterSynergyStripProps) {
  if (characters.length < 3 || pairPositionLabels.length < 3) {
    return null
  }

  return (
    <div className={className}>
      <div className="mb-2 flex items-start justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Character synergy
        </span>
        <div className="text-right">
          <p className="text-[11px] text-muted-foreground">같은 포지션 조합 점수</p>
          <p className="text-sm font-semibold text-cyan-300">
            {formatValue(samePositionAverageGetmmrScore)}
          </p>
          <p className="text-[11px] text-muted-foreground">
            raw {formatValue(samePositionAverageGetmmr, 2)}
          </p>
        </div>
      </div>

      {positionSummary && (
        <p className="mb-3 text-[11px] text-muted-foreground">
          포지션 조합: {positionSummary.replaceAll("|", " / ")}
          {typeof samePositionSampleCount === "number" && samePositionSampleCount > 0
            ? ` · 표본 ${samePositionSampleCount}개`
            : ""}
        </p>
      )}

      {(positionMainCombo || positionSubCombo) && (
        <div className="mb-3 grid gap-2 rounded-xl border border-border/70 bg-card/70 px-3 py-2 text-[11px] text-muted-foreground sm:grid-cols-2">
          <div>
            <span className="font-semibold text-foreground/80">Main</span>
            <p>{positionMainCombo?.replaceAll("_", " / ") ?? "N/A"}</p>
          </div>
          <div>
            <span className="font-semibold text-foreground/80">Sub</span>
            <p>{positionSubCombo?.replaceAll("_", " / ") ?? "N/A"}</p>
          </div>
        </div>
      )}

      {(typeof samePositionAverageDamage === "number" || typeof samePositionAverageHealAmount === "number") && (
        <div className="mb-3 grid gap-2 rounded-xl border border-cyan-400/15 bg-cyan-500/5 px-3 py-2 text-[11px] sm:grid-cols-2">
          <div>
            <span className="text-muted-foreground">같은 포지션 평균 총딜</span>
            <p className="font-semibold text-cyan-200">{formatValue(samePositionAverageDamage)}</p>
          </div>
          <div>
            <span className="text-muted-foreground">같은 포지션 평균 힐</span>
            <p className="font-semibold text-cyan-200">{formatValue(samePositionAverageHealAmount)}</p>
          </div>
        </div>
      )}

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="flex max-w-md flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Character
          </p>

          {pairIndexes.map(([leftIndex, rightIndex], index) => {
            const left = characters[leftIndex]
            const right = characters[rightIndex]

            if (!left || !right) {
              return null
            }

            return (
              <div
                key={`${left.name}-${right.name}`}
                className="rounded-xl border border-border/70 bg-card/70 px-3 py-2"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center">
                      <CharacterAvatar
                        name={left.name}
                        image={left.image}
                        weaponCode={left.weaponCode}
                        size="sm"
                      />
                      <div className="-ml-2">
                        <CharacterAvatar
                          name={right.name}
                          image={right.image}
                          weaponCode={right.weaponCode}
                          size="sm"
                        />
                      </div>
                    </div>

                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">
                        ({left.name} + {right.name})
                      </p>
                      <p className="text-[11px] text-muted-foreground">pair {index + 1}</p>
                    </div>
                  </div>

                  <div className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-2.5 py-1 text-xs font-semibold text-cyan-300">
                    {formatValue(values[index])}
                  </div>
                </div>
                <p className="mt-2 text-[11px] text-muted-foreground">
                  raw {formatValue(rawValues[index], 2)}
                </p>
              </div>
            )
          })}
        </div>

        <div className="flex max-w-md flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Position
          </p>

          {pairIndexes.map((_, index) => {
            const label = pairPositionLabels[index]
            if (!label) {
              return null
            }

            return (
              <div
                key={`${label}-${index}`}
                className="rounded-xl border border-border/70 bg-card/70 px-3 py-2"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">
                      ({label.replaceAll("+", " + ")})
                    </p>
                    <p className="text-[11px] text-muted-foreground">pair {index + 1}</p>
                  </div>

                  <div className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-2.5 py-1 text-xs font-semibold text-cyan-300">
                    {formatValue(values[index])}
                  </div>
                </div>
                <p className="mt-2 text-[11px] text-muted-foreground">
                  raw {formatValue(rawValues[index], 2)}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
