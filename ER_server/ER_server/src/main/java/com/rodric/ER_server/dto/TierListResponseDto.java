package com.rodric.ER_server.dto;

import java.util.List;

public class TierListResponseDto {

    private String windowStart;
    private String windowEnd;
    private int days;
    private List<TierListEntryDto> entries;

    public TierListResponseDto() {
    }

    public TierListResponseDto(String windowStart, String windowEnd, int days, List<TierListEntryDto> entries) {
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
        this.days = days;
        this.entries = entries;
    }

    public String getWindowStart() {
        return windowStart;
    }

    public void setWindowStart(String windowStart) {
        this.windowStart = windowStart;
    }

    public String getWindowEnd() {
        return windowEnd;
    }

    public void setWindowEnd(String windowEnd) {
        this.windowEnd = windowEnd;
    }

    public int getDays() {
        return days;
    }

    public void setDays(int days) {
        this.days = days;
    }

    public List<TierListEntryDto> getEntries() {
        return entries;
    }

    public void setEntries(List<TierListEntryDto> entries) {
        this.entries = entries;
    }
}
