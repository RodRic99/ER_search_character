package com.rodric.ER_server.service;

import com.rodric.ER_server.dto.TierListEntryDto;
import com.rodric.ER_server.dto.TierListResponseDto;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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

    private static final Logger log = LoggerFactory.getLogger(TierListService.class);

    private static final int DEFAULT_DAYS = 7;
    private static final DateTimeFormatter RESPONSE_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final int DIAMOND_PLUS_THRESHOLD = 5200;
    private static final int METEOR_PLUS_THRESHOLD = 6100;
    private static final int MITHRIL_PLUS_THRESHOLD = 6800;
    private static final String FIRST_WEEK_TABLE = "`1_week_tier`";
    private static final String SECOND_WEEK_TABLE = "`2_week_tier`";
    private static final List<TierRankTarget> TIER_RANK_TARGETS = List.of(
            new TierRankTarget("diamond", DIAMOND_PLUS_THRESHOLD),
            new TierRankTarget("meteor", METEOR_PLUS_THRESHOLD),
            new TierRankTarget("mithril", MITHRIL_PLUS_THRESHOLD)
    );
    private static final List<String> TIER_RANK_ORDER = List.of("S", "A", "B", "C", "D");
    private static final double PICK_RATE_HIGH_BAND_RATIO = 0.2;
    private static final double PICK_RATE_LOW_BAND_RATIO = 0.1;
    private static final double MIN_PICK_RATE_BAND = 0.15;
    private static final double RP_AVERAGE_BAND_RATIO = 0.05;
    private static final double RP_VERY_HIGH_BAND_RATIO = 0.12;
    private static final double MIN_RP_BAND = 0.5;

    private final JdbcTemplate jdbcTemplate;
    private final Object tierCacheRefreshLock = new Object();

    @PostConstruct
    public void initializeTierCacheTables() {
        createTierCacheTable(FIRST_WEEK_TABLE);
        createTierCacheTable(SECOND_WEEK_TABLE);
    }

    public TierListResponseDto getTierList(String rankTier) {
        String normalizedRankTier = normalizeRankTier(rankTier);
        ensureFirstWeekCache(normalizedRankTier);
        TierListWindow window = queryCacheWindow(FIRST_WEEK_TABLE, normalizedRankTier);
        List<TierListEntryDto> entries = queryCachedTierListEntries(FIRST_WEEK_TABLE, normalizedRankTier);

        return new TierListResponseDto(
                window.windowStart().format(RESPONSE_TIME_FORMATTER),
                window.windowEnd().format(RESPONSE_TIME_FORMATTER),
                DEFAULT_DAYS,
                entries
        );
    }

    @Scheduled(cron = "0 0 0 * * *", zone = "Asia/Seoul")
    @Transactional
    public void refreshDailyTierCaches() {
        refreshTierCaches();
    }

    @Transactional
    public void refreshTierCaches() {
        TierListWindow firstWeekWindow = resolveRecentWindow(DEFAULT_DAYS);
        TierListWindow secondWeekWindow = new TierListWindow(
                firstWeekWindow.windowStart().minusDays(DEFAULT_DAYS),
                firstWeekWindow.windowStart()
        );

        refreshTierCacheTable(FIRST_WEEK_TABLE, firstWeekWindow);
        refreshTierCacheTable(SECOND_WEEK_TABLE, secondWeekWindow);
        log.info("Refreshed tier cache tables for windows {} ~ {} and {} ~ {}",
                firstWeekWindow.windowStart(),
                firstWeekWindow.windowEnd(),
                secondWeekWindow.windowStart(),
                secondWeekWindow.windowEnd());
    }

    private void ensureFirstWeekCache(String rankTier) {
        Integer cacheCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM " + FIRST_WEEK_TABLE + " WHERE rank_tier = ?",
                Integer.class,
                rankTier
        );
        if (cacheCount == null || cacheCount == 0) {
            synchronized (tierCacheRefreshLock) {
                Integer refreshedCacheCount = jdbcTemplate.queryForObject(
                        "SELECT COUNT(*) FROM " + FIRST_WEEK_TABLE + " WHERE rank_tier = ?",
                        Integer.class,
                        rankTier
                );
                if (refreshedCacheCount == null || refreshedCacheCount == 0) {
                    refreshTierCaches();
                }
            }
        }
    }

    private void createTierCacheTable(String tableName) {
        jdbcTemplate.execute(
                "CREATE TABLE IF NOT EXISTS " + tableName + " ("
                        + "rank_tier VARCHAR(20) NOT NULL,"
                        + "ranking INT NOT NULL,"
                        + "characterNum INT NOT NULL,"
                        + "characterName VARCHAR(100) NOT NULL,"
                        + "tier VARCHAR(5) NOT NULL,"
                        + "rp_gain DOUBLE NOT NULL,"
                        + "pick_rate DOUBLE NOT NULL,"
                        + "win_rate DOUBLE NOT NULL,"
                        + "top3_rate DOUBLE NOT NULL,"
                        + "average_rank DOUBLE NOT NULL,"
                        + "average_damage DOUBLE NOT NULL,"
                        + "average_taken_damage DOUBLE NOT NULL,"
                        + "average_player_kill DOUBLE NOT NULL,"
                        + "window_start DATETIME NOT NULL,"
                        + "window_end DATETIME NOT NULL,"
                        + "computed_at DATETIME NOT NULL,"
                        + "PRIMARY KEY (rank_tier, ranking),"
                        + "INDEX idx_tier_cache_rank_character (rank_tier, characterNum)"
                        + ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"
        );
    }

    private void refreshTierCacheTable(String tableName, TierListWindow window) {
        jdbcTemplate.update("DELETE FROM " + tableName);

        for (TierRankTarget target : TIER_RANK_TARGETS) {
            List<TierListEntryDto> entries = queryTierListEntries(window, target.minimumRankTier());
            applyRankAndTier(entries);
            insertTierCacheEntries(tableName, target.rankTier(), window, entries);
        }
    }

    private void insertTierCacheEntries(
            String tableName,
            String rankTier,
            TierListWindow window,
            List<TierListEntryDto> entries
    ) {
        LocalDateTime computedAt = LocalDateTime.now();
        jdbcTemplate.batchUpdate(
                "INSERT INTO " + tableName + " ("
                        + "rank_tier, ranking, characterNum, characterName, tier, rp_gain, pick_rate, win_rate, "
                        + "top3_rate, average_rank, average_damage, average_taken_damage, average_player_kill, "
                        + "window_start, window_end, computed_at"
                        + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                entries,
                100,
                (preparedStatement, entry) -> {
                    preparedStatement.setString(1, rankTier);
                    preparedStatement.setInt(2, entry.getRank());
                    preparedStatement.setInt(3, entry.getCharacterNum());
                    preparedStatement.setString(4, entry.getCharacterName());
                    preparedStatement.setString(5, entry.getTier());
                    preparedStatement.setDouble(6, entry.getRpGain());
                    preparedStatement.setDouble(7, entry.getPickRate());
                    preparedStatement.setDouble(8, entry.getWinRate());
                    preparedStatement.setDouble(9, entry.getTop3Rate());
                    preparedStatement.setDouble(10, entry.getAverageRank());
                    preparedStatement.setDouble(11, entry.getAverageDamage());
                    preparedStatement.setDouble(12, entry.getAverageTakenDamage());
                    preparedStatement.setDouble(13, entry.getAveragePlayerKill());
                    preparedStatement.setObject(14, window.windowStart());
                    preparedStatement.setObject(15, window.windowEnd());
                    preparedStatement.setObject(16, computedAt);
                }
        );
    }

    private TierListWindow resolveRecentWindow(int days) {
        return jdbcTemplate.queryForObject(
                """
                SELECT
                    DATE_SUB(startDtm, INTERVAL ? DAY) AS window_start,
                    startDtm AS window_end
                FROM rankdb_v2
                WHERE matchingmode = 3
                ORDER BY startDtm DESC
                LIMIT 1
                """,
                (resultSet, rowNum) -> new TierListWindow(
                        resultSet.getTimestamp("window_start").toLocalDateTime(),
                        resultSet.getTimestamp("window_end").toLocalDateTime()
                ),
                days
        );
    }

    private TierListWindow queryCacheWindow(String tableName, String rankTier) {
        return jdbcTemplate.queryForObject(
                "SELECT MIN(window_start) AS window_start, MAX(window_end) AS window_end "
                        + "FROM " + tableName + " WHERE rank_tier = ?",
                (resultSet, rowNum) -> new TierListWindow(
                        resultSet.getTimestamp("window_start").toLocalDateTime(),
                        resultSet.getTimestamp("window_end").toLocalDateTime()
                ),
                rankTier
        );
    }

    private List<TierListEntryDto> queryCachedTierListEntries(String tableName, String rankTier) {
        return jdbcTemplate.query(
                "SELECT ranking, characterNum, characterName, tier, rp_gain, pick_rate, win_rate, "
                        + "top3_rate, average_rank, average_damage, average_taken_damage, average_player_kill "
                        + "FROM " + tableName + " WHERE rank_tier = ? ORDER BY ranking ASC",
                (resultSet, rowNum) -> new TierListEntryDto(
                        resultSet.getInt("ranking"),
                        resultSet.getInt("characterNum"),
                        resultSet.getString("characterName"),
                        resultSet.getString("tier"),
                        resultSet.getDouble("rp_gain"),
                        resultSet.getDouble("pick_rate"),
                        resultSet.getDouble("win_rate"),
                        resultSet.getDouble("top3_rate"),
                        resultSet.getDouble("average_rank"),
                        resultSet.getDouble("average_damage"),
                        resultSet.getDouble("average_taken_damage"),
                        resultSet.getDouble("average_player_kill")
                ),
                rankTier
        );
    }

    private List<TierListEntryDto> queryTierListEntries(TierListWindow window, int minimumRankTier) {
        return jdbcTemplate.query(
                """
                WITH recent_rows AS (
                    SELECT
                        characterNum,
                        mmrGain,
                        gamerank,
                        damageToPlayer,
                        damageFromPlayer,
                        playerKill
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

    private String normalizeRankTier(String rankTier) {
        if (rankTier == null) {
            return "diamond";
        }

        return switch (rankTier.trim().toLowerCase()) {
            case "mithril" -> "mithril";
            case "meteor" -> "meteor";
            case "diamond" -> "diamond";
            default -> "diamond";
        };
    }

    private int resolveMinimumRankTier(String rankTier) {
        return switch (normalizeRankTier(rankTier)) {
            case "mithril" -> MITHRIL_PLUS_THRESHOLD;
            case "meteor" -> METEOR_PLUS_THRESHOLD;
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

    private record TierRankTarget(String rankTier, int minimumRankTier) {
    }
}
