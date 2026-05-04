package com.rodric.ER_server.dto;

public class TierListEntryDto {

    private int rank;
    private int characterNum;
    private String characterName;
    private String tier;
    private double rpGain;
    private double pickRate;
    private double winRate;
    private double top3Rate;
    private double averageRank;
    private double averageDamage;
    private double averageTakenDamage;
    private double averagePlayerKill;

    public TierListEntryDto() {
    }

    public TierListEntryDto(
            int rank,
            int characterNum,
            String characterName,
            String tier,
            double rpGain,
            double pickRate,
            double winRate,
            double top3Rate,
            double averageRank,
            double averageDamage,
            double averageTakenDamage,
            double averagePlayerKill
    ) {
        this.rank = rank;
        this.characterNum = characterNum;
        this.characterName = characterName;
        this.tier = tier;
        this.rpGain = rpGain;
        this.pickRate = pickRate;
        this.winRate = winRate;
        this.top3Rate = top3Rate;
        this.averageRank = averageRank;
        this.averageDamage = averageDamage;
        this.averageTakenDamage = averageTakenDamage;
        this.averagePlayerKill = averagePlayerKill;
    }

    public int getRank() {
        return rank;
    }

    public void setRank(int rank) {
        this.rank = rank;
    }

    public int getCharacterNum() {
        return characterNum;
    }

    public void setCharacterNum(int characterNum) {
        this.characterNum = characterNum;
    }

    public String getCharacterName() {
        return characterName;
    }

    public void setCharacterName(String characterName) {
        this.characterName = characterName;
    }

    public String getTier() {
        return tier;
    }

    public void setTier(String tier) {
        this.tier = tier;
    }

    public double getRpGain() {
        return rpGain;
    }

    public void setRpGain(double rpGain) {
        this.rpGain = rpGain;
    }

    public double getPickRate() {
        return pickRate;
    }

    public void setPickRate(double pickRate) {
        this.pickRate = pickRate;
    }

    public double getWinRate() {
        return winRate;
    }

    public void setWinRate(double winRate) {
        this.winRate = winRate;
    }

    public double getTop3Rate() {
        return top3Rate;
    }

    public void setTop3Rate(double top3Rate) {
        this.top3Rate = top3Rate;
    }

    public double getAverageRank() {
        return averageRank;
    }

    public void setAverageRank(double averageRank) {
        this.averageRank = averageRank;
    }

    public double getAverageDamage() {
        return averageDamage;
    }

    public void setAverageDamage(double averageDamage) {
        this.averageDamage = averageDamage;
    }

    public double getAverageTakenDamage() {
        return averageTakenDamage;
    }

    public void setAverageTakenDamage(double averageTakenDamage) {
        this.averageTakenDamage = averageTakenDamage;
    }

    public double getAveragePlayerKill() {
        return averagePlayerKill;
    }

    public void setAveragePlayerKill(double averagePlayerKill) {
        this.averagePlayerKill = averagePlayerKill;
    }
}
