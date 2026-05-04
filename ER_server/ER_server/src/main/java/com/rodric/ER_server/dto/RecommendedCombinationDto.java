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
    private final String inputCombo;
    private final Double characterSynergy1;
    private final Double characterSynergy2;
    private final Double characterSynergy3;
    private Double samePositionAverageGetmmr;
    private Integer samePositionSampleCount;
    private String positionSummary;
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

    public void setSamePositionSampleCount(Integer samePositionSampleCount) {
        this.samePositionSampleCount = samePositionSampleCount;
    }

    public void setPositionSummary(String positionSummary) {
        this.positionSummary = positionSummary;
    }

    public void setPairPositionLabels(List<String> pairPositionLabels) {
        this.pairPositionLabels = pairPositionLabels;
    }
}
