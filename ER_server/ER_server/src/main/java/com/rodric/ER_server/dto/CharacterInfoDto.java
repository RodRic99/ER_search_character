package com.rodric.ER_server.dto;

public class CharacterInfoDto {

    private Integer characterNum;
    private String characterName;
    private String defaultPositionMain;
    private String defaultPositionSub;
    private Integer weaponCode;

    public CharacterInfoDto(Integer characterNum, String characterName, String defaultPositionMain, String defaultPositionSub) {
        this(characterNum, characterName, defaultPositionMain, defaultPositionSub, 0);
    }

    public CharacterInfoDto(Integer characterNum, String characterName, String defaultPositionMain, String defaultPositionSub, Integer weaponCode) {
        this.characterNum = characterNum;
        this.characterName = characterName;
        this.defaultPositionMain = defaultPositionMain;
        this.defaultPositionSub = defaultPositionSub;
        this.weaponCode = weaponCode;
    }

    public Integer getCharacterNum() {
        return characterNum;
    }

    public String getCharacterName() {
        return characterName;
    }

    public String getDefaultPositionMain() {
        return defaultPositionMain;
    }

    public String getDefaultPositionSub() {
        return defaultPositionSub;
    }

    public Integer getWeaponCode() {
        return weaponCode;
    }
}
