import { cn } from "@/lib/utils"
import { getWeaponInfo } from "@/lib/weapons"

interface CharacterAvatarProps {
  name: string
  image: string
  weaponCode?: number | null
  size?: "sm" | "md" | "lg"
  className?: string
}

const sizeClasses = {
  sm: {
    wrapper: "h-9 w-9 rounded-full",
    badge: "h-4 w-4 -right-0.5 -bottom-0.5 text-[9px]",
  },
  md: {
    wrapper: "h-12 w-12 rounded-full",
    badge: "h-5 w-5 -right-1 -bottom-1 text-[10px]",
  },
  lg: {
    wrapper: "h-16 w-16 rounded-full",
    badge: "h-6 w-6 -right-1 -bottom-1 text-[11px]",
  },
} as const

export function CharacterAvatar({
  name,
  image,
  weaponCode,
  size = "md",
  className,
}: CharacterAvatarProps) {
  const weapon = getWeaponInfo(weaponCode)
  const classes = sizeClasses[size]

  return (
    <div className={cn("relative shrink-0 overflow-visible", className)}>
      <div className={cn("overflow-hidden bg-secondary ring-1 ring-white/10", classes.wrapper)}>
        <img
          src={image}
          alt={name}
          className="h-full w-full object-cover"
        />
      </div>

      {weapon && (
        <div
          title={weapon.name}
          className={cn(
            "absolute flex items-center justify-center overflow-hidden rounded-full border border-white/20 bg-zinc-950 text-zinc-100 shadow-lg",
            classes.badge
          )}
        >
          {weapon.iconPath ? (
            <img
              src={weapon.iconPath}
              alt={weapon.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="font-bold leading-none">{weapon.shortLabel}</span>
          )}
        </div>
      )}
    </div>
  )
}
