package com.rodric.ER_server.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

@Component
public class PlayerApiClient {

    private static final Logger log = LoggerFactory.getLogger(PlayerApiClient.class);

    private final RestClient restClient;
    private final String userLookupPath;
    private final String playerStatPath;
    private final int seasonId;
    private final int matchingMode;

    public PlayerApiClient(
            @Value("${external-api.base-url}") String baseUrl,
            @Value("${external-api.api-key:}") String apiKey,
            @Value("${external-api.user-lookup-path:/v1/user/nickname}") String userLookupPath,
            @Value("${external-api.player-stat-path:/v2/user/stats/uid}") String playerStatPath,
            @Value("${external-api.season-id:37}") int seasonId,
            @Value("${external-api.matching-mode:3}") int matchingMode
    ) {
        RestClient.Builder builder = RestClient.builder().baseUrl(baseUrl);
        if (apiKey != null && !apiKey.isBlank()) {
            builder.defaultHeader("x-api-key", apiKey);
        }
        builder.defaultHeader(HttpHeaders.ACCEPT, "application/json");

        this.restClient = builder.build();
        this.userLookupPath = userLookupPath;
        this.playerStatPath = playerStatPath;
        this.seasonId = seasonId;
        this.matchingMode = matchingMode;
    }

    // 외부 API 조회 1단계: 닉네임으로 BSER userId를 찾는다.
    public String fetchUserIdByPlayerName(String playerName) {
        try {
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path(userLookupPath)
                            .queryParam("query", playerName)
                            .build())
                    .retrieve()
                    .body(Map.class);

            log.info("User lookup response for [{}]: {}", playerName, response);

            if (response == null || !(response.get("user") instanceof Map<?, ?> user)) {
                throw new IllegalArgumentException("userId not found for player: " + playerName + ", response=" + response);
            }

            Object userIdValue = user.get("userId");
            if (userIdValue == null) {
                throw new IllegalArgumentException("userId not found for player: " + playerName + ", response=" + response);
            }

            return String.valueOf(userIdValue);
        } catch (RestClientResponseException exception) {
            log.error("User lookup API failed. path={}, playerName={}, status={}, body={}",
                    userLookupPath, playerName, exception.getStatusCode(), exception.getResponseBodyAsString(), exception);
            throw new IllegalStateException("User lookup API failed: " + exception.getStatusCode() + " " + exception.getResponseBodyAsString(), exception);
        }
    }

    // 외부 API 조회 2단계: userId로 전적을 조회하고 사용량 기준 모스트3 캐릭터 번호를 뽑는다.
    public List<String> fetchMost3CharactersByUserId(String userId) {
        return fetchPlayerSeasonStatsByUserId(userId).most3CharacterCodes();
    }

    public PlayerSeasonStats fetchPlayerSeasonStatsByUserId(String userId) {
        try {
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path(playerStatPath + "/" + userId + "/" + seasonId + "/" + matchingMode)
                            .build())
                    .retrieve()
                    .body(Map.class);

            log.info("Player stat response for [{}]: {}", userId, response);

            if (response == null || !(response.get("userStats") instanceof List<?> userStats) || userStats.isEmpty()) {
                log.warn("userStats not found for userId={}, response={}", userId, response);
                return new PlayerSeasonStats(Collections.emptyList(), null);
            }

            Object firstStat = userStats.get(0);
            if (!(firstStat instanceof Map<?, ?> statMap) || !(statMap.get("characterStats") instanceof List<?> characterStats)) {
                log.warn("characterStats not found for userId={}, response={}", userId, response);
                return new PlayerSeasonStats(Collections.emptyList(), null);
            }

            List<String> most3CharacterCodes = characterStats.stream()
                    .filter(Map.class::isInstance)
                    .map(item -> (Map<?, ?>) item)
                    .sorted(Comparator.comparingLong(this::extractUsageCount).reversed())
                    .limit(3)
                    .map(this::extractCharacterCode)
                    .toList();

            return new PlayerSeasonStats(most3CharacterCodes, extractRankPoint(statMap));
        } catch (RestClientResponseException exception) {
            log.error("Player stat API failed. path={}, userId={}, status={}, body={}",
                    playerStatPath, userId, exception.getStatusCode(), exception.getResponseBodyAsString(), exception);
            throw new IllegalStateException("Player stat API failed: " + exception.getStatusCode() + " " + exception.getResponseBodyAsString(), exception);
        }
    }

    // BSER 응답 버전에 따라 사용 횟수 필드명이 다를 수 있어서 usages와 totalGames를 모두 확인한다.
    private long extractUsageCount(Map<?, ?> characterStat) {
        Object usages = characterStat.get("usages");
        if (usages instanceof Number number) {
            return number.longValue();
        }

        Object totalGames = characterStat.get("totalGames");
        if (totalGames instanceof Number number) {
            return number.longValue();
        }

        return 0L;
    }

    private String extractCharacterCode(Map<?, ?> characterStat) {
        Object characterCode = characterStat.get("characterCode");
        return String.valueOf(characterCode);
    }

    private Integer extractRankPoint(Map<?, ?> statMap) {
        Object rankPoint = statMap.get("rankPoint");
        if (rankPoint instanceof Number number) {
            return number.intValue();
        }

        Object mmr = statMap.get("mmr");
        if (mmr instanceof Number number) {
            return number.intValue();
        }

        Object mmrBefore = statMap.get("mmrBefore");
        if (mmrBefore instanceof Number number) {
            return number.intValue();
        }

        return null;
    }

    public record PlayerSeasonStats(List<String> most3CharacterCodes, Integer rankPoint) {
    }
}
