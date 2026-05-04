"use client"

type CharacterSynergyStripProps = {
  pairPositionLabels?: Array<string | null | undefined>
  values?: Array<number | null | undefined>
  positionSummary?: string
  samePositionAverageGetmmr?: number | null
  samePositionSampleCount?: number | null
  className?: string
}

const pairIndexes: Array<[number, number]> = [
  [0, 1],
  [0, 2],
  [1, 2],
]

const formatSynergyValue = (value?: number | null) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "N/A"
  }

  return value.toFixed(2)
}

export function CharacterSynergyStrip({
  pairPositionLabels = [],
  values = [],
  positionSummary,
  samePositionAverageGetmmr,
  samePositionSampleCount,
  className,
}: CharacterSynergyStripProps) {
  if (pairPositionLabels.length < 3) {
    return null
  }

  return (
    <div className={className}>
      <div className="mb-2 flex items-start justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Character synergy
        </span>
        <div className="text-right">
          <p className="text-[11px] text-muted-foreground">최근 7일 같은 포지션 평균</p>
          <p className="text-sm font-semibold text-cyan-300">
            {typeof samePositionAverageGetmmr === "number"
              ? samePositionAverageGetmmr.toFixed(2)
              : "N/A"}
          </p>
        </div>
      </div>

      {positionSummary && (
        <p className="mb-3 text-[11px] text-muted-foreground">
          포지션 조합: {positionSummary.replaceAll("|", " / ")}
          {typeof samePositionSampleCount === "number" && samePositionSampleCount > 0
            ? ` · 표본 ${samePositionSampleCount}팀`
            : ""}
        </p>
      )}

      <div className="flex max-w-md flex-col gap-2">
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
                  <p className="text-[11px] text-muted-foreground">
                    pair {index + 1}
                  </p>
                </div>

                <div className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-2.5 py-1 text-xs font-semibold text-cyan-300">
                  {formatSynergyValue(values[index])}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
