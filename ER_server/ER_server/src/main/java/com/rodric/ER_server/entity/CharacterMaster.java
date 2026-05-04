package com.rodric.ER_server.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "character_master")
public class CharacterMaster {

    @Id
    @Column(name = "characterNum")
    private Integer characterNum;

    @Column(name = "characterName", nullable = false, length = 100)
    private String characterName;

    @Column(name = "default_position_main", length = 20)
    private String defaultPositionMain;

    @Column(name = "default_position_sub", length = 20)
    private String defaultPositionSub;

    protected CharacterMaster() {
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
}
