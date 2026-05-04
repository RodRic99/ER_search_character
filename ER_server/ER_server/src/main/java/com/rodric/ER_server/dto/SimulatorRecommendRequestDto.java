package com.rodric.ER_server.dto;

import java.util.List;

public class SimulatorRecommendRequestDto {

    private List<List<Integer>> characterPools;

    public List<List<Integer>> getCharacterPools() {
        return characterPools;
    }

    public void setCharacterPools(List<List<Integer>> characterPools) {
        this.characterPools = characterPools;
    }
}
