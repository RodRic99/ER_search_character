package com.rodric.ER_server.dto;

import lombok.Setter;

import java.util.List;

@Setter
public class PlayerMost3ResponseDto {

    // BSER에서 조회한 플레이어별 모스트3 결과.
    private List<PlayerMost3ItemDto> players;

    // 미리 계산된 모델 결과 CSV에서 조회한 팀 조합 추천 결과.
    private List<RecommendedCombinationDto> recommendedCombinations;
    private String highestRankPointPlayerName;
    private Integer highestRankPoint;
    private boolean highestRankModelPredictionEnabled;

    public PlayerMost3ResponseDto() {
    }

    public PlayerMost3ResponseDto(List<PlayerMost3ItemDto> players) {
        this.players = players;
    }

    public PlayerMost3ResponseDto(List<PlayerMost3ItemDto> players, List<RecommendedCombinationDto> recommendedCombinations) {
        this.players = players;
        this.recommendedCombinations = recommendedCombinations;
    }

    public List<PlayerMost3ItemDto> getPlayers() {
        return players;
    }

    public void setPlayers(List<PlayerMost3ItemDto> players) {
        this.players = players;
    }

    public List<RecommendedCombinationDto> getRecommendedCombinations() {
        return recommendedCombinations;
    }

    public String getHighestRankPointPlayerName() {
        return highestRankPointPlayerName;
    }

    public void setHighestRankPointPlayerName(String highestRankPointPlayerName) {
        this.highestRankPointPlayerName = highestRankPointPlayerName;
    }

    public Integer getHighestRankPoint() {
        return highestRankPoint;
    }

    public void setHighestRankPoint(Integer highestRankPoint) {
        this.highestRankPoint = highestRankPoint;
    }

    public boolean isHighestRankModelPredictionEnabled() {
        return highestRankModelPredictionEnabled;
    }

    public void setHighestRankModelPredictionEnabled(boolean highestRankModelPredictionEnabled) {
        this.highestRankModelPredictionEnabled = highestRankModelPredictionEnabled;
    }
}
