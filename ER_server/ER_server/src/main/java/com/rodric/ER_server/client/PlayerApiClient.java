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
    private static final int MAX_API_RETRIES = 3;
    private static final long RETRY_DELAY_MILLIS = 1500L;

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

    public String fetchUserIdByPlayerName(String playerName) {
        for (int attempt = 1; attempt <= MAX_API_RETRIES; attempt++) {
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
                if (shouldRetry(exception, attempt)) {
                    log.warn("User lookup API hit rate limit. playerName={}, attempt={}/{}. Retrying after {} ms.",
                            playerName, attempt, MAX_API_RETRIES, RETRY_DELAY_MILLIS);
                    sleepBeforeRetry();
                    continue;
                }

                log.error("User lookup API failed. path={}, playerName={}, status={}, body={}",
                        userLookupPath, playerName, exception.getStatusCode(), exception.getResponseBodyAsString(), exception);
                throw new IllegalStateException("User lookup API failed: " + exception.getStatusCode() + " " + exception.getResponseBodyAsString(), exception);
            }
        }

        throw new IllegalStateException("User lookup API failed after retries for player: " + playerName);
    }

    public List<String> fetchMost3CharactersByUserId(String userId) {
        return fetchPlayerSeasonStatsByUserId(userId).most3CharacterCodes();
    }

    public PlayerSeasonStats fetchPlayerSeasonStatsByUserId(String userId) {
        for (int attempt = 1; attempt <= MAX_API_RETRIES; attempt++) {
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
                if (shouldRetry(exception, attempt)) {
                    log.warn("Player stat API hit rate limit. userId={}, attempt={}/{}. Retrying after {} ms.",
                            userId, attempt, MAX_API_RETRIES, RETRY_DELAY_MILLIS);
                    sleepBeforeRetry();
                    continue;
                }

                log.error("Player stat API failed. path={}, userId={}, status={}, body={}",
                        playerStatPath, userId, exception.getStatusCode(), exception.getResponseBodyAsString(), exception);
                throw new IllegalStateException("Player stat API failed: " + exception.getStatusCode() + " " + exception.getResponseBodyAsString(), exception);
            }
        }

        throw new IllegalStateException("Player stat API failed after retries for userId: " + userId);
    }

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

    private boolean shouldRetry(RestClientResponseException exception, int attempt) {
        return exception.getStatusCode().value() == 429 && attempt < MAX_API_RETRIES;
    }

    private void sleepBeforeRetry() {
        try {
            Thread.sleep(RETRY_DELAY_MILLIS);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("API retry delay interrupted.", exception);
        }
    }

    public record PlayerSeasonStats(List<String> most3CharacterCodes, Integer rankPoint) {
    }
}
