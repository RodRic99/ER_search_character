export type Character = {
  id: number
  name: string
  image: string
  weaponCode?: number
}

type CharacterEntry = {
  id: number
  name: string
  image: string
  weaponCode?: number
  aliases: string[]
}

const characterEntries: CharacterEntry[] = [
  { id: 1, name: "재키", image: "/character_img/Jackie_Mini_00.png", weaponCode: 16, aliases: ["Jackie"] },
  { id: 2, name: "아야", image: "/character_img/Aya_Mini_00.png", weaponCode: 10, aliases: ["Aya"] },
  { id: 3, name: "현우", image: "/character_img/Hyunwoo_Mini_00.png", weaponCode: 21, aliases: ["Hyunwoo"] },
  { id: 4, name: "매그너스", image: "/character_img/Mini_Magnus_00.png", weaponCode: 13, aliases: ["Magnus"] },
  { id: 5, name: "피오라", image: "/character_img/Fiora_Mini_00.png", weaponCode: 6, aliases: ["Fiora"] },
  { id: 6, name: "나딘", image: "/character_img/Nadine_Mini_00.png", weaponCode: 8, aliases: ["Nadine"] },
  { id: 7, name: "자히르", image: "/character_img/Zahir_Mini_00.png", weaponCode: 1, aliases: ["Zahir"] },
  { id: 8, name: "하트", image: "/character_img/Hart_Mini_00.png", weaponCode: 22, aliases: ["Hart"] },
  { id: 9, name: "아이솔", image: "/character_img/Isol_Mini_00.png", weaponCode: 10, aliases: ["Isol"] },
  { id: 10, name: "리다이린", image: "/character_img/Li Dailin_Mini_00.png", weaponCode: 1, aliases: ["Li Dailin", "LiDailin"] },
  { id: 11, name: "유키", image: "/character_img/Yuki_Mini_00.png", weaponCode: 16, aliases: ["Yuki"] },
  { id: 12, name: "혜진", image: "/character_img/Hyejin_Mini_00.png", weaponCode: 7, aliases: ["Hyejin"] },
  { id: 13, name: "쇼우", image: "/character_img/Xiukai_Mini_00.png", weaponCode: 15, aliases: ["Xiukai"] },
  { id: 14, name: "시셀라", image: "/character_img/Sissela_Mini_00.png", weaponCode: 21, aliases: ["Sissela"] },
  { id: 15, name: "키아라", image: "/character_img/Chiara_Mini_00.png", weaponCode: 6, aliases: ["Chiara"] },
  { id: 16, name: "아드리아나", image: "/character_img/Adriana_Mini_00.png", weaponCode: 9, aliases: ["Adriana"] },
  { id: 17, name: "쇼이치", image: "/character_img/Shoichi_Mini_00.png", weaponCode: 5, aliases: ["Shoichi"] },
  { id: 18, name: "실비아", image: "/character_img/Silvia_Mini_00.png", weaponCode: 15, aliases: ["Silvia"] },
  { id: 19, name: "엠마", image: "/character_img/Emma_Mini_00.png", weaponCode: 6, aliases: ["Emma"] },
  { id: 20, name: "레녹스", image: "/character_img/Lenox_Mini_00.png", weaponCode: 4, aliases: ["Lenox"] },
  { id: 21, name: "로지", image: "/character_img/Rozzi_Mini_00.png", weaponCode: 9, aliases: ["Rozzi"] },
  { id: 22, name: "루크", image: "/character_img/Luke_Mini_00.png", weaponCode: 3, aliases: ["Luke"] },
  { id: 23, name: "캐시", image: "/character_img/Cathy_Mini_00.png", weaponCode: 15, aliases: ["Cathy"] },
  { id: 24, name: "아델라", image: "/character_img/Adela_Mini_00.png", weaponCode: 21, aliases: ["Adela"] },
  { id: 25, name: "버니스", image: "/character_img/bERnice_Mini_00.png", weaponCode: 11, aliases: ["Bernice"] },
  { id: 26, name: "바바라", image: "/character_img/Barbara_Mini_00.png", weaponCode: 9, aliases: ["Barbara"] },
  { id: 27, name: "알렉스", image: "/character_img/Alex_Mini_00.png", weaponCode: 16, aliases: ["Alex"] },
  { id: 28, name: "수아", image: "/character_img/Sua_Mini_00.png", weaponCode: 3, aliases: ["Sua"] },
  { id: 29, name: "레온", image: "/character_img/Leon_Mini_00.png", weaponCode: 1, aliases: ["Leon"] },
  { id: 30, name: "일레븐", image: "/character_img/Eleven_Mini_00.png", weaponCode: 13, aliases: ["Eleven"] },
  { id: 31, name: "리오", image: "/character_img/Rio_Mini_00.png", weaponCode: 7, aliases: ["Rio"] },
  { id: 32, name: "윌리엄", image: "/character_img/William_Mini_00.png", weaponCode: 5, aliases: ["William"] },
  { id: 33, name: "니키", image: "/character_img/Nicky_Mini_00.png", weaponCode: 1, aliases: ["Nicky"] },
  { id: 34, name: "나타폰", image: "/character_img/Nathapon_Mini_00.png", weaponCode: 23, aliases: ["Nathapon"] },
  { id: 35, name: "얀", image: "/character_img/Jan_Mini_00.png", weaponCode: 2, aliases: ["Jan"] },
  { id: 36, name: "이바", image: "/character_img/Eva_Mini_00.png", weaponCode: 5, aliases: ["Eva"] },
  { id: 37, name: "다니엘", image: "/character_img/Daniel_Mini_00.png", weaponCode: 15, aliases: ["Daniel"] },
  { id: 38, name: "제니", image: "/character_img/Jenny_Mini_00.png", weaponCode: 9, aliases: ["Jenny"] },
  { id: 39, name: "카밀로", image: "/character_img/Camilo_Mini_00.png", weaponCode: 21, aliases: ["Camilo"] },
  { id: 40, name: "클로에", image: "/character_img/Chloe_Mini_00.png", weaponCode: 6, aliases: ["Chloe"] },
  { id: 41, name: "요한", image: "/character_img/Johann_Mini_00.png", weaponCode: 24, aliases: ["Johann"] },
  { id: 42, name: "비앙카", image: "/character_img/Bianca_Mini_00.png", weaponCode: 24, aliases: ["Bianca"] },
  { id: 43, name: "셀린", image: "/character_img/Celine_Mini_00.png", weaponCode: 5, aliases: ["Celine"] },
  { id: 44, name: "에키온", image: "/character_img/Echion_Mini_00.png", weaponCode: 25, aliases: ["Echion"] },
  { id: 45, name: "마이", image: "/character_img/Mai_Mini_00.png", weaponCode: 4, aliases: ["Mai"] },
  { id: 46, name: "에이든", image: "/character_img/Aiden_Mini_00.png", weaponCode: 16, aliases: ["Aiden"] },
  { id: 47, name: "라우라", image: "/character_img/Laura_Mini_00.png", weaponCode: 4, aliases: ["Laura"] },
  { id: 48, name: "띠아", image: "/character_img/Tia_Mini_00.png", weaponCode: 3, aliases: ["Tia"] },
  { id: 49, name: "펠릭스", image: "/character_img/Skin_Mini_002.png", weaponCode: 19, aliases: ["Felix"] },
  { id: 50, name: "엘레나", image: "/character_img/Elena_Mini_00.png", weaponCode: 21, aliases: ["Elena"] },
  { id: 51, name: "프리야", image: "/character_img/Priya_Mini_00.png", weaponCode: 22, aliases: ["Priya"] },
  { id: 52, name: "아디나", image: "/character_img/Adina_Mini_00.png", weaponCode: 24, aliases: ["Adina"] },
  { id: 53, name: "마커스", image: "/character_img/Markus_Mini_00.png", weaponCode: 14, aliases: ["Markus"] },
  { id: 54, name: "칼라", image: "/character_img/Karla_Mini_00.png", weaponCode: 8, aliases: ["Karla"] },
  { id: 55, name: "에스텔", image: "/character_img/Estelle_Mini_00.png", weaponCode: 14, aliases: ["Estelle"] },
  { id: 56, name: "피올로", image: "/character_img/Piolo_Mini_00.png", weaponCode: 20, aliases: ["Piolo"] },
  { id: 57, name: "마르티나", image: "/character_img/Martina_Mini_00.png", weaponCode: 23, aliases: ["Martina"] },
  { id: 58, name: "헤이즈", image: "/character_img/Haze_Mini_00.png", weaponCode: 10, aliases: ["Haze"] },
  { id: 59, name: "아이작", image: "/character_img/Isaac_Mini_00.png", weaponCode: 2, aliases: ["Isaac"] },
  { id: 60, name: "타지아", image: "/character_img/Tazia_Mini_00.png", weaponCode: 6, aliases: ["Tazia"] },
  { id: 61, name: "이렘", image: "/character_img/Irem_Mini_00.png", weaponCode: 5, aliases: ["Irem"] },
  { id: 62, name: "테오도르", image: "/character_img/Theodore_Mini_00.png", weaponCode: 11, aliases: ["Theodore"] },
  { id: 63, name: "이안", image: "/character_img/Ly anh_Mini_00.png", weaponCode: 15, aliases: ["Ian", "Ly anh", "Ly Anh"] },
  { id: 64, name: "바냐", image: "/character_img/Vanya_Mini_00.png", weaponCode: 24, aliases: ["Vanya"] },
  { id: 65, name: "데비마를렌", image: "/character_img/DebiMarlene_Mini_00.png", weaponCode: 16, aliases: ["DebiMarlene", "Debi & Marlene", "Debi and Marlene", "데비&마를렌"] },
  { id: 66, name: "아르다", image: "/character_img/Arda_Mini_00.png", weaponCode: 24, aliases: ["Arda"] },
  { id: 67, name: "아비게일", image: "/character_img/Abigail_Mini_00.png", weaponCode: 14, aliases: ["Abigail"] },
  { id: 68, name: "알론소", image: "/character_img/Alonso_Mini_00.png", weaponCode: 1, aliases: ["Alonso"] },
  { id: 69, name: "레니", image: "/character_img/Leni_Mini_00.png", weaponCode: 9, aliases: ["Leni"] },
  { id: 70, name: "츠바메", image: "/character_img/Tsubame_Mini_00.png", weaponCode: 6, aliases: ["Tsubame"] },
  { id: 71, name: "케네스", image: "/character_img/Kenneth_Mini_00.png", weaponCode: 14, aliases: ["Kenneth"] },
  { id: 72, name: "카티야", image: "/character_img/Katja_Mini_00.png", weaponCode: 11, aliases: ["Katja"] },
  { id: 73, name: "살럿", image: "/character_img/Charlotte_Mini_00.png", weaponCode: 24, aliases: ["Charlotte", "샬럿"] },
  { id: 74, name: "다르코", image: "/character_img/Darko_Mini_00.png", weaponCode: 3, aliases: ["Darko"] },
  { id: 75, name: "르노어", image: "/character_img/Lenore_Mini_00.png", weaponCode: 22, aliases: ["Lenore"] },
  { id: 76, name: "가넷", image: "/character_img/Garnet_Mini_00.png", weaponCode: 3, aliases: ["Garnet"] },
  { id: 77, name: "유민", image: "/character_img/Mini_YuMin_00.png", weaponCode: 24, aliases: ["YuMin", "Yumin"] },
  { id: 78, name: "히스이", image: "/character_img/Mini_Hisui_00.png", weaponCode: 16, aliases: ["Hisui"] },
  { id: 79, name: "유스티나", image: "/character_img/Mini_Justyna_00.png", weaponCode: 8, aliases: ["Justyna"] },
  { id: 80, name: "이슈트반", image: "/character_img/Mini_Istvan_00.png", weaponCode: 19, aliases: ["Istvan"] },
  { id: 81, name: "니아", image: "/character_img/Mini_NiaH_00.png", weaponCode: 9, aliases: ["Nia", "NiaH"] },
  { id: 82, name: "슈린", image: "/character_img/Mini_Xuelin_00.png", weaponCode: 21, aliases: ["Xuelin", "Shurin"] },
  { id: 83, name: "헨리", image: "/character_img/Mini_Henry_00.png", weaponCode: 6, aliases: ["Henry"] },
  { id: 84, name: "블레어", image: "/character_img/Mini_Blair_00.png", weaponCode: 18, aliases: ["Blair"] },
  { id: 85, name: "미르카", image: "/character_img/Mirka_Mini_00.png", weaponCode: 13, aliases: ["Mirka"] },
  { id: 86, name: "펜릴", image: "/character_img/Mini_Fenrir_00.png", weaponCode: 1, aliases: ["Fenrir"] },
  { id: 87, name: "코렐라인", image: "/character_img/Mini_Coraline_00.png", weaponCode: 24, aliases: ["Coraline"] },
]

const normalizeCharacterName = (name: string) =>
  name
    .split(" - ")[0]
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ")

const aliasToEntryMap = Object.fromEntries(
  characterEntries.flatMap((character) => [
    [normalizeCharacterName(character.name), character],
    ...character.aliases.map((alias) => [normalizeCharacterName(alias), character] as const),
  ])
)

export const getCharacterImage = (name: string) => {
  const normalizedName = normalizeCharacterName(name)
  return aliasToEntryMap[normalizedName]?.image ?? "/placeholder.svg"
}

export const getCharacterWeaponCode = (name: string) => {
  const normalizedName = normalizeCharacterName(name)
  return aliasToEntryMap[normalizedName]?.weaponCode
}

export const getCharacterWeaponCodeById = (id: number) =>
  characterEntries.find((character) => character.id === id)?.weaponCode

export const characters: Character[] = characterEntries.map((character) => ({
  id: character.id,
  name: character.name,
  image: character.image,
  weaponCode: character.weaponCode,
}))
