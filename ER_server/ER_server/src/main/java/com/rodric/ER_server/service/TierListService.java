package com.rodric.ER_server.service;

import com.rodric.ER_server.dto.TierListEntryDto;
import com.rodric.ER_server.dto.TierListResponseDto;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TierListService {

    private static final int DEFAULT_DAYS = 7;
    private static final DateTimeFormatter RESPONSE_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final int DIAMOND_PLUS_THRESHOLD = 5200;
    private static final int METEOR_PLUS_THRESHOLD = 6100;
    private static final int MITHRIL_PLUS_THRESHOLD = 6800;
    private static final List<String> TIER_RANK_ORDER = List.of("S", "A", "B", "C", "D");
    private static final double PICK_RATE_HIGH_BAND_RATIO = 0.2;
    private static final double PICK_RATE_LOW_BAND_RATIO = 0.1;
    private static final double MIN_PICK_RATE_BAND = 0.15;
    private static final double RP_AVERAGE_BAND_RATIO = 0.05;
    private static final double RP_VERY_HIGH_BAND_RATIO = 0.12;
    private static final double MIN_RP_BAND = 0.5;

    private final JdbcTemplate jdbcTemplate;

    public TierListResponseDto getTierList(String rankTier) {
        TierListWindow window = resolveRecentWindow(DEFAULT_DAYS);
        int minimumRankTier = resolveMinimumRankTier(rankTier);
        List<TierListEntryDto> entries = queryTierListEntries(window, minimumRankTier);
        applyRankAndTier(entries);

        return new TierListResponseDto(
                window.windowStart().format(RESPONSE_TIME_FORMATTER),
                window.windowEnd().format(RESPONSE_TIME_FORMATTER),
                DEFAULT_DAYS,
                entries
        );
    }

    private TierListWindow resolveRecentWindow(int days) {
        return jdbcTemplate.queryForObject(
                """
                SELECT
                    DATE_SUB(MAX(startDtm), INTERVAL ? DAY) AS window_start,
                    MAX(startDtm) AS window_end
                FROM rankdb_v2
                WHERE matchingmode = 3
                """,
                (resultSet, rowNum) -> new TierListWindow(
                        resultSet.getTimestamp("window_start").toLocalDateTime(),
                        resultSet.getTimestamp("window_end").toLocalDateTime()
                ),
                days
        );
    }

    private List<TierListEntryDto> queryTierListEntries(TierListWindow window, int minimumRankTier) {
        return jdbcTemplate.query(
                """
                WITH recent_rows AS (
                    SELECT *
                    FROM rankdb_v2
                    WHERE startDtm >= ?
                      AND startDtm <= ?
                      AND matchingmode = 3
                      AND rankPoint >= ?
                ),
                total_picks AS (
                    SELECT COUNT(*) AS total_pick_count
                    FROM recent_rows
                    WHERE characterNum IS NOT NULL
                )
                SELECT
                    cm.characterNum,
                    cm.characterName,
                    AVG(rr.mmrGain) AS rp_gain,
                    COUNT(*) * 100.0 / tp.total_pick_count AS pick_rate,
                    AVG(CASE WHEN rr.gamerank = 1 THEN 100.0 ELSE 0.0 END) AS win_rate,
                    AVG(CASE WHEN rr.gamerank <= 3 THEN 100.0 ELSE 0.0 END) AS top3_rate,
                    AVG(rr.gamerank) AS average_rank,
                    AVG(rr.damageToPlayer) AS average_damage,
                    AVG(rr.damageFromPlayer) AS average_taken_damage,
                    AVG(rr.playerKill) AS average_player_kill
                FROM recent_rows rr
                JOIN character_master cm
                  ON cm.characterNum = rr.characterNum
                CROSS JOIN total_picks tp
                WHERE rr.characterNum IS NOT NULL
                GROUP BY cm.characterNum, cm.characterName, tp.total_pick_count
                ORDER BY rp_gain DESC, pick_rate DESC, cm.characterNum ASC
                """,
                (resultSet, rowNum) -> mapEntry(resultSet),
                window.windowStart(),
                window.windowEnd(),
                minimumRankTier
        );
    }

    private int resolveMinimumRankTier(String rankTier) {
        if (rankTier == null) {
            return DIAMOND_PLUS_THRESHOLD;
        }

        return switch (rankTier.trim().toLowerCase()) {
            case "mithril" -> MITHRIL_PLUS_THRESHOLD;
            case "meteor" -> METEOR_PLUS_THRESHOLD;
            case "diamond" -> DIAMOND_PLUS_THRESHOLD;
            default -> DIAMOND_PLUS_THRESHOLD;
        };
    }

    private TierListEntryDto mapEntry(ResultSet resultSet) throws SQLException {
        return new TierListEntryDto(
                0,
                resultSet.getInt("characterNum"),
                resultSet.getString("characterName"),
                "",
                resultSet.getDouble("rp_gain"),
                resultSet.getDouble("pick_rate"),
                resultSet.getDouble("win_rate"),
                resultSet.getDouble("top3_rate"),
                resultSet.getDouble("average_rank"),
                resultSet.getDouble("average_damage"),
                resultSet.getDouble("average_taken_damage"),
                resultSet.getDouble("average_player_kill")
        );
    }

    private void applyRankAndTier(List<TierListEntryDto> entries) {
        double averagePickRate = entries.stream()
                .mapToDouble(TierListEntryDto::getPickRate)
                .average()
                .orElse(0.0);
        double averageRpGain = entries.stream()
                .mapToDouble(TierListEntryDto::getRpGain)
                .average()
                .orElse(0.0);
        List<TierListEntryDto> rankedEntries = new ArrayList<>(entries);

        for (int index = 0; index < rankedEntries.size(); index++) {
            TierListEntryDto entry = rankedEntries.get(index);
            entry.setTier(resolveTier(entry, averagePickRate, averageRpGain));
        }

        rankedEntries.sort(Comparator
                .comparingInt((TierListEntryDto entry) -> resolveTierOrder(entry.getTier()))
                .thenComparing(TierListEntryDto::getRpGain, Comparator.reverseOrder())
                .thenComparing(TierListEntryDto::getPickRate, Comparator.reverseOrder())
                .thenComparing(TierListEntryDto::getCharacterNum));

        for (int index = 0; index < rankedEntries.size(); index++) {
            rankedEntries.get(index).setRank(index + 1);
        }
    }

    private int resolveTierOrder(String tier) {
        int index = TIER_RANK_ORDER.indexOf(tier);
        return index >= 0 ? index : TIER_RANK_ORDER.size();
    }

    private String resolveTier(TierListEntryDto entry, double averagePickRate, double averageRpGain) {
        double highPickBand = Math.max(averagePickRate * PICK_RATE_HIGH_BAND_RATIO, MIN_PICK_RATE_BAND);
        double lowPickBand = Math.max(averagePickRate * PICK_RATE_LOW_BAND_RATIO, MIN_PICK_RATE_BAND);
        boolean isHighPickRate = entry.getPickRate() >= averagePickRate + highPickBand;
        boolean isAverageOrBetterPickRate = entry.getPickRate() >= averagePickRate;
        boolean isLowPickRate = entry.getPickRate() < averagePickRate - lowPickBand;
        double rpBand = Math.max(Math.abs(averageRpGain) * RP_AVERAGE_BAND_RATIO, MIN_RP_BAND);
        double veryHighRpBand = Math.max(Math.abs(averageRpGain) * RP_VERY_HIGH_BAND_RATIO, MIN_RP_BAND * 2);
        boolean isVeryHighRpGain = entry.getRpGain() > averageRpGain + veryHighRpBand;
        boolean isHighRpGain = entry.getRpGain() > averageRpGain + rpBand;
        boolean isAverageRpGain = entry.getRpGain() >= averageRpGain - rpBand
                && entry.getRpGain() <= averageRpGain + rpBand;

        if ((isHighPickRate && isVeryHighRpGain)
                || (isAverageOrBetterPickRate && isHighRpGain)) {
            return "S";
        }
        if ((isHighPickRate && (isHighRpGain || isAverageRpGain))
                || (isAverageOrBetterPickRate && isVeryHighRpGain)
                || (!isLowPickRate && isHighRpGain)) {
            return "A";
        }
        if ((!isLowPickRate && isAverageRpGain) || (isLowPickRate && isHighRpGain)) {
            return "B";
        }
        return "C";
    }

    private record TierListWindow(LocalDateTime windowStart, LocalDateTime windowEnd) {
    }
}
