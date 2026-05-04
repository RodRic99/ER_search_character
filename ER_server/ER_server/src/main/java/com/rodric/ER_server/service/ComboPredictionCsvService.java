package com.rodric.ER_server.service;

import com.rodric.ER_server.dto.RecommendedCombinationDto;
import com.rodric.ER_server.dto.CharacterInfoDto;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class ComboPredictionCsvService {

    // 기존 호출부를 최대한 덜 흔들기 위해 서비스 이름은 유지하되,
    // 내부 구현은 CSV가 아니라 날짜별 MySQL 예측 테이블 조회로 교체한다.
    private static final int DEFAULT_LIMIT = 5;
    private static final int PARTIAL_SLOT_LIMIT = 10;
    private static final Pattern TABLE_NAME_PATTERN = Pattern.compile("^\\d{4}_\\d{2}_\\d{2}_all_predict$");
    private static final DateTimeFormatter TABLE_DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy_MM_dd");

    private final JdbcTemplate jdbcTemplate;
    private final NamedParameterJdbcTemplate namedParameterJdbcTemplate;
    private final CharacterMasterService characterMasterService;

    public List<RecommendedCombinationDto> recommendCombinations(List<List<Integer>> playerMost3CharacterNums) {
        List<List<Integer>> sanitizedPools = sanitizePools(playerMost3CharacterNums);
        if (sanitizedPools.isEmpty()) {
            return List.of();
        }

        return queryRecommendations(
                resolvePredictionTableName(),
                List.of(sanitizedPools),
                DEFAULT_LIMIT
        );
    }

    public List<RecommendedCombinationDto> recommendCombinationsForSimulator(List<List<Integer>> characterPools) {
        List<List<Integer>> sanitizedPools = sanitizePools(characterPools);
        if (sanitizedPools.size() < 2) {
            return List.of();
        }

        int limit = sanitizedPools.size() >= 3 ? DEFAULT_LIMIT : PARTIAL_SLOT_LIMIT;
        return queryRecommendations(
                resolvePredictionTableName(),
                buildSimulatorScenarios(sanitizedPools),
                limit
        );
    }

    private List<RecommendedCombinationDto> queryRecommendations(
            String tableName,
            List<List<List<Integer>>> scenarios,
            int limit
    ) {
        if (scenarios.isEmpty()) {
            return List.of();
        }

        MapSqlParameterSource parameters = new MapSqlParameterSource();
        String whereClause = buildScenarioWhereClause(scenarios, parameters);
        parameters.addValue("limit", limit);

        String sql = """
                SELECT
                    characterNum_1,
                    weaponCode_1,
                    characterNum_2,
                    weaponCode_2,
                    characterNum_3,
                    weaponCode_3,
                    predicted_avg_getmmr,
                    input_combo,
                    character_combo_names,
                    weapon_combo_names,
                    character_synergy_1,
                    character_synergy_2,
                    character_synergy_3
                FROM `%s`
                WHERE %s
                ORDER BY predicted_avg_getmmr DESC
                LIMIT :limit
                """.formatted(tableName, whereClause);

        List<RecommendedCombinationDto> combinations =
                namedParameterJdbcTemplate.query(sql, parameters, this::mapRecommendedCombination);
        enrichPositionAverages(combinations);
        return combinations;
    }

    private String resolvePredictionTableName() {
        String todayTableName = LocalDate.now().format(TABLE_DATE_FORMATTER) + "_all_predict";
        List<String> exactTodayTables = jdbcTemplate.query(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = ?
                """,
                (resultSet, rowNum) -> resultSet.getString("table_name"),
                todayTableName
        );

        if (!exactTodayTables.isEmpty()) {
            return exactTodayTables.get(0);
        }

        List<String> fallbackTables = jdbcTemplate.query(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name REGEXP '^[0-9]{4}_[0-9]{2}_[0-9]{2}_all_predict$'
                ORDER BY table_name DESC
                LIMIT 1
                """,
                (resultSet, rowNum) -> resultSet.getString("table_name")
        );

        if (fallbackTables.isEmpty()) {
            throw new IllegalStateException("No all_predict tables were found in the current database.");
        }

        String tableName = fallbackTables.get(0);
        if (!TABLE_NAME_PATTERN.matcher(tableName).matches()) {
            throw new IllegalStateException("Unexpected prediction table name: " + tableName);
        }

        return tableName;
    }

    private String buildScenarioWhereClause(
            List<List<List<Integer>>> scenarios,
            MapSqlParameterSource parameters
    ) {
        List<String> scenarioClauses = new ArrayList<>();

        for (int scenarioIndex = 0; scenarioIndex < scenarios.size(); scenarioIndex++) {
            List<List<Integer>> scenario = scenarios.get(scenarioIndex);
            List<String> slotClauses = new ArrayList<>();

            for (int slotIndex = 0; slotIndex < scenario.size(); slotIndex++) {
                String parameterName = "scenario" + scenarioIndex + "_slot" + slotIndex;
                parameters.addValue(parameterName, scenario.get(slotIndex));
                slotClauses.add("""
                        (
                            characterNum_1 IN (:%1$s)
                            OR characterNum_2 IN (:%1$s)
                            OR characterNum_3 IN (:%1$s)
                        )
                        """.formatted(parameterName).trim());
            }

            scenarioClauses.add("(" + String.join(" AND ", slotClauses) + ")");
        }

        return String.join(" OR ", scenarioClauses);
    }

    private RecommendedCombinationDto mapRecommendedCombination(ResultSet resultSet, int rowNum) throws SQLException {
        return new RecommendedCombinationDto(
                List.of(
                        resultSet.getInt("characterNum_1"),
                        resultSet.getInt("characterNum_2"),
                        resultSet.getInt("characterNum_3")
                ),
                List.of(
                        resultSet.getInt("weaponCode_1"),
                        resultSet.getInt("weaponCode_2"),
                        resultSet.getInt("weaponCode_3")
                ),
                splitNames(resultSet.getString("character_combo_names")),
                splitNames(resultSet.getString("weapon_combo_names")),
                resultSet.getDouble("predicted_avg_getmmr"),
                resultSet.getString("input_combo"),
                getNullableDouble(resultSet, "character_synergy_1"),
                getNullableDouble(resultSet, "character_synergy_2"),
                getNullableDouble(resultSet, "character_synergy_3")
        );
    }

    private List<List<Integer>> sanitizePools(List<List<Integer>> pools) {
        if (pools == null) {
            return List.of();
        }

        return pools.stream()
                .filter(pool -> pool != null && !pool.isEmpty())
                .map(pool -> pool.stream()
                        .filter(characterNum -> characterNum != null && characterNum > 0)
                        .distinct()
                        .toList())
                .filter(pool -> !pool.isEmpty())
                .toList();
    }

    private List<List<List<Integer>>> buildSimulatorScenarios(List<List<Integer>> characterPools) {
        List<List<List<Integer>>> scenarios = new ArrayList<>();
        scenarios.add(characterPools);

        Set<Integer> usedCharacterNums = new HashSet<>();
        List<List<Integer>> deduplicatedScenario = new ArrayList<>();

        for (List<Integer> pool : characterPools) {
            List<Integer> filteredPool = pool.stream()
                    .filter(characterNum -> !usedCharacterNums.contains(characterNum))
                    .toList();

            if (filteredPool.isEmpty()) {
                return scenarios;
            }

            deduplicatedScenario.add(filteredPool);
            usedCharacterNums.addAll(filteredPool);
        }

        if (!deduplicatedScenario.equals(characterPools)) {
            scenarios.add(deduplicatedScenario);
        }

        return scenarios;
    }

    private List<String> splitNames(String value) {
        if (value == null || value.isBlank()) {
            return List.of();
        }

        return Arrays.stream(value.split("_"))
                .map(String::trim)
                .toList();
    }

    private Double getNullableDouble(ResultSet resultSet, String columnLabel) throws SQLException {
        double value = resultSet.getDouble(columnLabel);
        return resultSet.wasNull() ? null : value;
    }

    private void enrichPositionAverages(List<RecommendedCombinationDto> combinations) {
        Map<String, PositionAverageStats> statsBySummary = new HashMap<>();

        for (RecommendedCombinationDto combination : combinations) {
            List<String> roleNames = resolveRoleNames(combination.getCharacterNums());
            String positionSummary = resolvePositionSummary(roleNames);
            combination.setPairPositionLabels(buildPairPositionLabels(roleNames));
            combination.setPositionSummary(positionSummary);

            if (positionSummary == null || positionSummary.isBlank()) {
                continue;
            }

            PositionAverageStats stats = statsBySummary.computeIfAbsent(
                    positionSummary,
                    this::queryWeeklyAverageForSamePositions
            );
            combination.setSamePositionAverageGetmmr(stats.averageGetmmr());
            combination.setSamePositionSampleCount(stats.sampleCount());
        }
    }

    private List<String> resolveRoleNames(List<Integer> characterNums) {
        if (characterNums == null || characterNums.size() < 3) {
            return List.of();
        }

        List<CharacterInfoDto> characterInfos = characterMasterService.findCharactersByCodes(
                characterNums.stream().map(String::valueOf).toList()
        );
        if (characterInfos.size() < 3) {
            return List.of();
        }

        return characterInfos.stream()
                .map(CharacterInfoDto::getDefaultPositionSub)
                .map(this::normalizePosition)
                .toList();
    }

    private String resolvePositionSummary(List<String> roleNames) {
        if (roleNames == null || roleNames.size() < 3) {
            return null;
        }

        return roleNames.stream()
                .sorted()
                .reduce((left, right) -> left + "|" + right)
                .orElse(null);
    }

    private String normalizePosition(String position) {
        if (position == null || position.isBlank()) {
            return "unknown";
        }

        return position.trim().toLowerCase(Locale.ROOT);
    }

    private PositionAverageStats queryWeeklyAverageForSamePositions(String positionSummary) {
        return jdbcTemplate.queryForObject(
                """
                WITH recent_window AS (
                    SELECT
                        DATE_SUB(MAX(startDtm), INTERVAL 7 DAY) AS window_start,
                        MAX(startDtm) AS window_end
                    FROM rankdb_v2
                    WHERE matchingmode = 3
                ),
                team_position_stats AS (
                    SELECT
                        rr.gameid,
                        rr.teamNumber,
                        GROUP_CONCAT(
                            COALESCE(LOWER(TRIM(cm.default_position_sub)), 'unknown')
                            ORDER BY COALESCE(LOWER(TRIM(cm.default_position_sub)), 'unknown')
                            SEPARATOR '|'
                        ) AS position_summary,
                        AVG(rr.mmrGain) AS team_avg_getmmr,
                        COUNT(*) AS member_count
                    FROM rankdb_v2 rr
                    JOIN character_master cm
                      ON cm.characterNum = rr.characterNum
                    CROSS JOIN recent_window rw
                    WHERE rr.matchingmode = 3
                      AND rr.startDtm >= rw.window_start
                      AND rr.startDtm <= rw.window_end
                      AND rr.characterNum IS NOT NULL
                    GROUP BY rr.gameid, rr.teamNumber
                    HAVING member_count = 3
                )
                SELECT
                    AVG(team_avg_getmmr) AS same_position_avg_getmmr,
                    COUNT(*) AS sample_count
                FROM team_position_stats
                WHERE position_summary = ?
                """,
                (resultSet, rowNum) -> new PositionAverageStats(
                        getNullableDouble(resultSet, "same_position_avg_getmmr"),
                        resultSet.getInt("sample_count")
                ),
                positionSummary
        );
    }

    private List<String> buildPairPositionLabels(List<String> roleNames) {
        if (roleNames == null || roleNames.size() < 3) {
            return List.of();
        }

        return List.of(
                roleNames.get(0) + "+" + roleNames.get(1),
                roleNames.get(0) + "+" + roleNames.get(2),
                roleNames.get(1) + "+" + roleNames.get(2)
        );
    }

    private record PositionAverageStats(Double averageGetmmr, Integer sampleCount) {
    }
}
