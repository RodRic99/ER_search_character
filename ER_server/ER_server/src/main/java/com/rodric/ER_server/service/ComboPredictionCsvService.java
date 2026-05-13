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
import java.util.Comparator;
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
    private static final String SCORE_METRIC_PREDICTED = "predicted_avg_getmmr";
    private static final String SCORE_METRIC_CHARACTER_SYNERGY = "character_synergy";
    private static final String SCORE_METRIC_POSITION_AVG_GETMMR = "position_avg_getmmr";
    private static final double PREDICTED_SCORE_WEIGHT = 0.6;
    private static final double POSITION_SCORE_WEIGHT = 0.4;

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
        applyAbsoluteScores(combinations);
        combinations.sort(
                Comparator.comparing(
                        (RecommendedCombinationDto dto) -> dto.getOverallScore() != null ? dto.getOverallScore() : Double.NEGATIVE_INFINITY
                ).reversed()
        );
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
        Map<String, PositionAverageStats> statsBySignature = new HashMap<>();

        for (RecommendedCombinationDto combination : combinations) {
            List<CharacterRoleInfo> roleInfos = resolveRoleInfos(
                    combination.getCharacterNums(),
                    combination.getWeaponCodes()
            );
            PositionSignature positionSignature = buildPositionSignature(roleInfos);
            combination.setPairPositionLabels(buildPairPositionLabels(roleInfos));
            combination.setPositionSummary(positionSignature.positionFullCombo());
            combination.setPositionMainCombo(positionSignature.positionMainCombo());
            combination.setPositionSubCombo(positionSignature.positionSubCombo());

            if (positionSignature.signature() == null || positionSignature.signature().isBlank()) {
                continue;
            }

            PositionAverageStats stats = statsBySignature.computeIfAbsent(
                    positionSignature.signature(),
                    this::queryCachedPositionStats
            );
            combination.setSamePositionAverageGetmmr(stats.averageGetmmr());
            combination.setSamePositionSampleCount(stats.sampleCount());
            combination.setSamePositionAverageDamage(stats.averageTotalDamage());
            combination.setSamePositionAverageHealAmount(stats.averageTotalHealAmount());
        }
    }

    private void applyAbsoluteScores(List<RecommendedCombinationDto> combinations) {
        Map<String, ScoreRange> scoreRanges = queryLatestScoreRanges();

        for (RecommendedCombinationDto combination : combinations) {
            Double predictedScore = mapToScore(combination.getPredictedAvgGetmmr(), scoreRanges.get(SCORE_METRIC_PREDICTED));
            combination.setPredictedAvgGetmmrScore(predictedScore);
            combination.setCharacterSynergy1Score(
                    mapToScore(combination.getCharacterSynergy1(), scoreRanges.get(SCORE_METRIC_CHARACTER_SYNERGY))
            );
            combination.setCharacterSynergy2Score(
                    mapToScore(combination.getCharacterSynergy2(), scoreRanges.get(SCORE_METRIC_CHARACTER_SYNERGY))
            );
            combination.setCharacterSynergy3Score(
                    mapToScore(combination.getCharacterSynergy3(), scoreRanges.get(SCORE_METRIC_CHARACTER_SYNERGY))
            );
            Double positionScore = mapToScore(combination.getSamePositionAverageGetmmr(), scoreRanges.get(SCORE_METRIC_POSITION_AVG_GETMMR));
            combination.setSamePositionAverageGetmmrScore(positionScore);
            combination.setOverallScore(computeOverallScore(predictedScore, positionScore));
        }
    }

    private Double computeOverallScore(Double predictedScore, Double positionScore) {
        if (predictedScore == null && positionScore == null) {
            return null;
        }
        if (predictedScore == null) {
            return positionScore;
        }
        if (positionScore == null) {
            return predictedScore;
        }

        double overallScore = (predictedScore * PREDICTED_SCORE_WEIGHT) + (positionScore * POSITION_SCORE_WEIGHT);
        return Math.round(overallScore * 10.0) / 10.0;
    }

    private Map<String, ScoreRange> queryLatestScoreRanges() {
        List<ScoreRange> ranges = jdbcTemplate.query(
                """
                SELECT
                    metric_name,
                    min_value,
                    max_value,
                    p05_value,
                    p95_value
                FROM daily_score_metric_cache
                WHERE cutoff_date = (
                    SELECT MAX(cutoff_date)
                    FROM daily_score_metric_cache
                )
                """,
                (resultSet, rowNum) -> new ScoreRange(
                        resultSet.getString("metric_name"),
                        getNullableDouble(resultSet, "min_value"),
                        getNullableDouble(resultSet, "max_value"),
                        getNullableDouble(resultSet, "p05_value"),
                        getNullableDouble(resultSet, "p95_value")
                )
        );

        Map<String, ScoreRange> scoreRangeMap = new HashMap<>();
        for (ScoreRange range : ranges) {
            scoreRangeMap.put(range.metricName(), range);
        }
        return scoreRangeMap;
    }

    private Double mapToScore(Double rawValue, ScoreRange scoreRange) {
        if (rawValue == null || scoreRange == null) {
            return null;
        }

        double lowerBound = scoreRange.p05Value() != null ? scoreRange.p05Value() : scoreRange.minValue();
        double upperBound = scoreRange.p95Value() != null ? scoreRange.p95Value() : scoreRange.maxValue();

        if (lowerBound >= upperBound) {
            return 100.0;
        }

        double clampedValue = Math.max(lowerBound, Math.min(rawValue, upperBound));
        double normalizedScore = ((clampedValue - lowerBound) / (upperBound - lowerBound)) * 100.0;
        return Math.round(normalizedScore * 10.0) / 10.0;
    }

    private List<CharacterRoleInfo> resolveRoleInfos(List<Integer> characterNums, List<Integer> weaponCodes) {
        if (characterNums == null || weaponCodes == null || characterNums.size() < 3 || characterNums.size() != weaponCodes.size()) {
            return List.of();
        }

        List<CharacterInfoDto> characterInfos = characterMasterService.findCharactersByNumsAndWeapons(
                characterNums,
                weaponCodes
        );
        if (characterInfos.size() < 3) {
            return List.of();
        }

        return characterInfos.stream()
                .map(characterInfo -> new CharacterRoleInfo(
                        normalizePosition(characterInfo.getDefaultPositionMain()),
                        normalizePosition(characterInfo.getDefaultPositionSub())
                ))
                .toList();
    }

    private PositionSignature buildPositionSignature(List<CharacterRoleInfo> roleInfos) {
        if (roleInfos == null || roleInfos.size() < 3) {
            return new PositionSignature(null, null, null, null);
        }

        String positionMainCombo = roleInfos.stream()
                .map(CharacterRoleInfo::main)
                .sorted()
                .reduce((left, right) -> left + "_" + right)
                .orElse(null);

        String positionSubCombo = roleInfos.stream()
                .map(CharacterRoleInfo::sub)
                .sorted()
                .reduce((left, right) -> left + "_" + right)
                .orElse(null);

        String positionFullCombo = roleInfos.stream()
                .map(roleInfo -> roleInfo.main() + ":" + roleInfo.sub())
                .sorted()
                .reduce((left, right) -> left + "|" + right)
                .orElse(null);

        String signature = null;
        if (positionMainCombo != null && positionSubCombo != null && positionFullCombo != null) {
            signature = positionMainCombo + "||" + positionSubCombo + "||" + positionFullCombo;
        }

        return new PositionSignature(signature, positionMainCombo, positionSubCombo, positionFullCombo);
    }

    private String normalizePosition(String position) {
        if (position == null || position.isBlank()) {
            return "unknown";
        }

        return position.trim().toLowerCase(Locale.ROOT);
    }

    private PositionAverageStats queryCachedPositionStats(String positionSignature) {
        return jdbcTemplate.queryForObject(
                """
                SELECT
                    avg_getmmr AS same_position_avg_getmmr,
                    match_count AS sample_count,
                    avg_total_damage AS same_position_avg_total_damage,
                    avg_total_healAmount AS same_position_avg_total_healAmount
                FROM daily_position_synergy_cache
                WHERE cutoff_date = (
                    SELECT MAX(cutoff_date)
                    FROM daily_position_synergy_cache
                )
                  AND position_signature = ?
                """,
                (resultSet, rowNum) -> new PositionAverageStats(
                        getNullableDouble(resultSet, "same_position_avg_getmmr"),
                        resultSet.getInt("sample_count"),
                        getNullableDouble(resultSet, "same_position_avg_total_damage"),
                        getNullableDouble(resultSet, "same_position_avg_total_healAmount")
                ),
                positionSignature
        );
    }

    private List<String> buildPairPositionLabels(List<CharacterRoleInfo> roleInfos) {
        if (roleInfos == null || roleInfos.size() < 3) {
            return List.of();
        }

        return List.of(
                roleInfos.get(0).sub() + "+" + roleInfos.get(1).sub(),
                roleInfos.get(0).sub() + "+" + roleInfos.get(2).sub(),
                roleInfos.get(1).sub() + "+" + roleInfos.get(2).sub()
        );
    }

    private record CharacterRoleInfo(String main, String sub) {
    }

    private record PositionSignature(
            String signature,
            String positionMainCombo,
            String positionSubCombo,
            String positionFullCombo
    ) {
    }

    private record PositionAverageStats(
            Double averageGetmmr,
            Integer sampleCount,
            Double averageTotalDamage,
            Double averageTotalHealAmount
    ) {
    }

    private record ScoreRange(
            String metricName,
            Double minValue,
            Double maxValue,
            Double p05Value,
            Double p95Value
    ) {
    }
}
