package com.rodric.ER_server.dto;

import lombok.RequiredArgsConstructor;
import lombok.Setter;

import java.util.List;
@RequiredArgsConstructor
@Setter
public class PlayerMost3RequestDto {

    private List<String> playerNames;

    public List<String> getPlayerNames() {
        return playerNames;
    }

    public void setPlayerNames(List<String> playerNames) {
        this.playerNames = playerNames;
    }
}
