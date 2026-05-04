export type WeaponInfo = {
  code: number
  name: string
  shortLabel: string
  iconPath?: string
}

const weaponInfoByCode: Record<number, WeaponInfo> = {
  1: { code: 1, name: "글러브", shortLabel: "글", iconPath: "/weapon_icons/01. Glove.png" },
  2: { code: 2, name: "톤파", shortLabel: "톤", iconPath: "/weapon_icons/02. Tonfa.png" },
  3: { code: 3, name: "방망이", shortLabel: "방", iconPath: "/weapon_icons/03. Bat.png" },
  4: { code: 4, name: "채찍", shortLabel: "채", iconPath: "/weapon_icons/05. Whip.png" },
  5: { code: 5, name: "투척", shortLabel: "투", iconPath: "/weapon_icons/06. Throwing.png" },
  6: { code: 6, name: "암기", shortLabel: "암", iconPath: "/weapon_icons/07. Shuriken.png" },
  7: { code: 7, name: "활", shortLabel: "활", iconPath: "/weapon_icons/08. Bow.png" },
  8: { code: 8, name: "석궁", shortLabel: "석", iconPath: "/weapon_icons/09. Crossbow.png" },
  9: { code: 9, name: "권총", shortLabel: "권", iconPath: "/weapon_icons/10. Pistol.png" },
  10: { code: 10, name: "돌격 소총", shortLabel: "돌", iconPath: "/weapon_icons/11. Assault Rifle.png" },
  11: { code: 11, name: "저격총", shortLabel: "저", iconPath: "/weapon_icons/12. Sniper Rifle.png" },
  13: { code: 13, name: "망치", shortLabel: "망", iconPath: "/weapon_icons/04. Hammer.png" },
  14: { code: 14, name: "도끼", shortLabel: "도", iconPath: "/weapon_icons/13. Axe.png" },
  15: { code: 15, name: "단검", shortLabel: "단", iconPath: "/weapon_icons/14. Dagger.png" },
  16: { code: 16, name: "양손검", shortLabel: "양", iconPath: "/weapon_icons/15. Twohanded Sword.png" },
  // 폴암 전용 아이콘 파일이 따로 없어서 창 계열 아이콘을 임시 공용 사용.
  17: { code: 17, name: "폴암", shortLabel: "폴", iconPath: "/weapon_icons/17. Spear.png" },
  18: { code: 18, name: "쌍검", shortLabel: "쌍", iconPath: "/weapon_icons/16. Dual Sword.png" },
  19: { code: 19, name: "창", shortLabel: "창", iconPath: "/weapon_icons/17. Spear.png" },
  20: { code: 20, name: "쌍절곤", shortLabel: "절", iconPath: "/weapon_icons/18. Nunchaku.png" },
  21: { code: 21, name: "레이피어", shortLabel: "레", iconPath: "/weapon_icons/19. Rapier.png" },
  22: { code: 22, name: "기타", shortLabel: "기", iconPath: "/weapon_icons/20. Guitar.png" },
  23: { code: 23, name: "카메라", shortLabel: "카", iconPath: "/weapon_icons/21. Camera.png" },
  24: { code: 24, name: "아르카나", shortLabel: "아", iconPath: "/weapon_icons/22. Arcana.png" },
  25: { code: 25, name: "VF의수", shortLabel: "V", iconPath: "/weapon_icons/23. VF Prosthetic.png" },
}

export const getWeaponInfo = (weaponCode?: number | null) =>
  weaponCode ? weaponInfoByCode[weaponCode] : undefined
