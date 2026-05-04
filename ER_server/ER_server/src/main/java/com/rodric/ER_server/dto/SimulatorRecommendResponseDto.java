package com.rodric.ER_server.dto;

import java.util.List;

public class SimulatorRecommendResponseDto {

    private List<List<Integer>> characterPools;
    private List<RecommendedCombinationDto> recommendedCombinations;

    public SimulatorRecommendResponseDto() {
    }

    public SimulatorRecommendResponseDto(
            List<List<Integer>> characterPools,
            List<RecommendedCombinationDto> recommendedCombinations
    ) {
        this.characterPools = characterPools;
        this.recommendedCombinations = recommendedCombinations;
    }

    public List<List<Integer>> getCharacterPools() {
        return characterPools;
    }

    public void setCharacterPools(List<List<Integer>> characterPools) {
        this.characterPools = characterPools;
    }

    public List<RecommendedCombinationDto> getRecommendedCombinations() {
        return recommendedCombinations;
    }

    public void setRecommendedCombinations(List<RecommendedCombinationDto> recommendedCombinations) {
        this.recommendedCombinations = recommendedCombinations;
    }
}
