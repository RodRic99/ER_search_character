package com.rodric.ER_server.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class RecommendedCombinationDto {

    // 매일 미리 계산된 조합 예측 CSV에서 가져온 추천 팀 조합이다.
    private final List<Integer> characterNums;
    private final List<Integer> weaponCodes;
    private final List<String> characterNames;
    private final List<String> weaponNames;
    private final double predictedAvgGetmmr;
    private Double overallScore;
    private Double predictedAvgGetmmrScore;
    private final String inputCombo;
    private final Double characterSynergy1;
    private final Double characterSynergy2;
    private final Double characterSynergy3;
    private Double characterSynergy1Score;
    private Double characterSynergy2Score;
    private Double characterSynergy3Score;
    private Double samePositionAverageGetmmr;
    private Double samePositionAverageGetmmrScore;
    private Integer samePositionSampleCount;
    private String positionSummary;
    private String positionMainCombo;
    private String positionSubCombo;
    private Double samePositionAverageDamage;
    private Double samePositionAverageHealAmount;
    private List<String> pairPositionLabels;

    public RecommendedCombinationDto(
            List<Integer> characterNums,
            List<Integer> weaponCodes,
            List<String> characterNames,
            List<String> weaponNames,
            double predictedAvgGetmmr,
            String inputCombo,
            Double characterSynergy1,
            Double characterSynergy2,
            Double characterSynergy3
    ) {
        this.characterNums = characterNums;
        this.weaponCodes = weaponCodes;
        this.characterNames = characterNames;
        this.weaponNames = weaponNames;
        this.predictedAvgGetmmr = predictedAvgGetmmr;
        this.inputCombo = inputCombo;
        this.characterSynergy1 = characterSynergy1;
        this.characterSynergy2 = characterSynergy2;
        this.characterSynergy3 = characterSynergy3;
    }

    public void setSamePositionAverageGetmmr(Double samePositionAverageGetmmr) {
        this.samePositionAverageGetmmr = samePositionAverageGetmmr;
    }

    public void setPredictedAvgGetmmrScore(Double predictedAvgGetmmrScore) {
        this.predictedAvgGetmmrScore = predictedAvgGetmmrScore;
    }

    public void setCharacterSynergy1Score(Double characterSynergy1Score) {
        this.characterSynergy1Score = characterSynergy1Score;
    }

    public void setCharacterSynergy2Score(Double characterSynergy2Score) {
        this.characterSynergy2Score = characterSynergy2Score;
    }

    public void setCharacterSynergy3Score(Double characterSynergy3Score) {
        this.characterSynergy3Score = characterSynergy3Score;
    }

    public void setSamePositionAverageGetmmrScore(Double samePositionAverageGetmmrScore) {
        this.samePositionAverageGetmmrScore = samePositionAverageGetmmrScore;
    }

    public void setOverallScore(Double overallScore) {
        this.overallScore = overallScore;
    }

    public Double getOverallScore() {
        return overallScore;
    }

    public void setSamePositionSampleCount(Integer samePositionSampleCount) {
        this.samePositionSampleCount = samePositionSampleCount;
    }

    public void setPositionSummary(String positionSummary) {
        this.positionSummary = positionSummary;
    }

    public void setPositionMainCombo(String positionMainCombo) {
        this.positionMainCombo = positionMainCombo;
    }

    public void setPositionSubCombo(String positionSubCombo) {
        this.positionSubCombo = positionSubCombo;
    }

    public void setSamePositionAverageDamage(Double samePositionAverageDamage) {
        this.samePositionAverageDamage = samePositionAverageDamage;
    }

    public void setSamePositionAverageHealAmount(Double samePositionAverageHealAmount) {
        this.samePositionAverageHealAmount = samePositionAverageHealAmount;
    }

    public void setPairPositionLabels(List<String> pairPositionLabels) {
        this.pairPositionLabels = pairPositionLabels;
    }
}
