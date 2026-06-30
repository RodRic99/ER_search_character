package com.rodric.ER_server.service;

import com.rodric.ER_server.client.PlayerApiClient;
import com.rodric.ER_server.client.PredictApiClient;
import com.rodric.ER_server.dto.CharacterInfoDto;
import com.rodric.ER_server.dto.ModelPredictRequestDto;
import com.rodric.ER_server.dto.PlayerMost3ItemDto;
import com.rodric.ER_server.dto.PlayerMost3ResponseDto;
import com.rodric.ER_server.dto.RecommendedCombinationDto;
import com.rodric.ER_server.dto.SimulatorRecommendResponseDto;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class PlayerStatInfoService {

    private static final Logger log = LoggerFactory.getLogger(PlayerStatInfoService.class);
    private static final long API_DELAY_MILLIS = 1500L;

    @Value("${app.features.enable-highest-rank-model-predict:false}")
    private boolean enableHighestRankModelPredict;

    private final PlayerApiClient playerApiClient;
    private final PredictApiClient predictApiClient;
    private final CharacterMasterService characterMasterService;
    private final ComboPredictionCsvService comboPredictionCsvService;

    public PlayerMost3ResponseDto getMost3ForPlayers(List<String> playerNames) {
        List<String> sanitizedPlayerNames = validateAndSanitizePlayerNames(playerNames);

        List<List<Integer>> playerMost3CharacterNums = new ArrayList<>();
        List<PlayerMost3ItemDto> players = new ArrayList<>();

        for (String playerName : sanitizedPlayerNames) {
            try {
                players.add(buildPlayerMost3Item(playerName, playerMost3CharacterNums));
            } catch (IllegalArgumentException | IllegalStateException exception) {
                log.warn("Skipping player in multi-search. playerName={}, reason={}", playerName, exception.getMessage());
            }
        }

        if (players.isEmpty()) {
            throw new IllegalStateException("Could not load stats for any requested players.");
        }

        List<RecommendedCombinationDto> recommendedCombinations = playerMost3CharacterNums.isEmpty()
                ? List.of()
                : comboPredictionCsvService.recommendCombinations(playerMost3CharacterNums);

        PlayerMost3ResponseDto responseDto = new PlayerMost3ResponseDto(players, recommendedCombinations);
        Optional<PlayerMost3ItemDto> highestRankPointPlayer = findHighestRankPointPlayer(players);
        responseDto.setHighestRankPointPlayerName(highestRankPointPlayer.map(PlayerMost3ItemDto::getPlayerName).orElse(null));
        responseDto.setHighestRankPoint(highestRankPointPlayer.map(PlayerMost3ItemDto::getRankPoint).orElse(null));
        responseDto.setHighestRankModelPredictionEnabled(enableHighestRankModelPredict);

        if (enableHighestRankModelPredict) {
            highestRankPointPlayer.ifPresent(this::attachPredictionForHighestRankPlayer);
        }

        return responseDto;
    }

    public SimulatorRecommendResponseDto recommendForSimulator(List<List<Integer>> characterPools) {
        List<List<Integer>> sanitizedPools = validateAndSanitizeCharacterPools(characterPools);
        if (sanitizedPools.size() < 2) {
            return new SimulatorRecommendResponseDto(sanitizedPools, List.of());
        }

        List<RecommendedCombinationDto> recommendedCombinations =
                comboPredictionCsvService.recommendCombinationsForSimulator(sanitizedPools);

        return new SimulatorRecommendResponseDto(sanitizedPools, recommendedCombinations);
    }

    private List<String> validateAndSanitizePlayerNames(List<String> playerNames) {
        if (playerNames == null) {
            throw new IllegalArgumentException("playerNames must contain 1 to 3 names.");
        }

        List<String> sanitizedPlayerNames = playerNames.stream()
                .filter(playerName -> playerName != null && !playerName.isBlank())
                .map(String::trim)
                .toList();

        if (sanitizedPlayerNames.isEmpty() || sanitizedPlayerNames.size() > 3) {
            throw new IllegalArgumentException("playerNames must contain 1 to 3 non-blank names.");
        }

        return sanitizedPlayerNames;
    }

    private PlayerMost3ItemDto buildPlayerMost3Item(String playerName, List<List<Integer>> playerMost3CharacterNums) {
        String userId = playerApiClient.fetchUserIdByPlayerName(playerName);
        sleepBetweenRequests();
        PlayerApiClient.PlayerSeasonStats playerSeasonStats = playerApiClient.fetchPlayerSeasonStatsByUserId(userId);
        List<String> most3CharacterCodes = playerSeasonStats.most3CharacterCodes();
        List<Integer> most3CharacterNums = parseCharacterNums(most3CharacterCodes);

        if (!most3CharacterNums.isEmpty()) {
            playerMost3CharacterNums.add(most3CharacterNums);
        }

        List<String> most3Characters = characterMasterService.findCharactersByCodes(most3CharacterCodes).stream()
                .map(CharacterInfoDto::getCharacterName)
                .toList();
        sleepBetweenRequests();

        return new PlayerMost3ItemDto(
                playerName,
                userId,
                playerSeasonStats.rankPoint(),
                most3Characters,
                most3CharacterNums
        );
    }

    private List<List<Integer>> validateAndSanitizeCharacterPools(List<List<Integer>> characterPools) {
        if (characterPools == null || characterPools.isEmpty()) {
            throw new IllegalArgumentException("characterPools must contain at least one pool.");
        }

        List<List<Integer>> sanitizedPools = characterPools.stream()
                .filter(pool -> pool != null && !pool.isEmpty())
                .map(pool -> pool.stream()
                        .filter(characterNum -> characterNum != null && characterNum > 0)
                        .distinct()
                        .toList())
                .filter(pool -> !pool.isEmpty())
                .toList();

        if (sanitizedPools.isEmpty() || sanitizedPools.size() > 3) {
            throw new IllegalArgumentException("characterPools must contain 1 to 3 non-empty pools.");
        }

        return sanitizedPools;
    }

    private Optional<PlayerMost3ItemDto> findHighestRankPointPlayer(List<PlayerMost3ItemDto> players) {
        return players.stream()
                .filter(player -> player.getRankPoint() != null)
                .max(Comparator.comparingInt(PlayerMost3ItemDto::getRankPoint));
    }

    private void attachPredictionForHighestRankPlayer(PlayerMost3ItemDto player) {
        ModelPredictRequestDto requestDto = buildHighestRankModelPredictRequest(player);
        if (requestDto == null) {
            return;
        }

        Map<String, Object> prediction = predictApiClient.predict(requestDto);
        player.setPrediction(prediction);
    }

    private ModelPredictRequestDto buildHighestRankModelPredictRequest(PlayerMost3ItemDto player) {
        List<Integer> characterNums = player.getMost3CharacterNums();
        if (characterNums == null || characterNums.size() < 3) {
            return null;
        }

        List<CharacterInfoDto> characterInfos = characterMasterService.findCharactersByCodes(
                characterNums.stream().limit(3).map(String::valueOf).toList()
        );
        if (characterInfos.size() < 3) {
            return null;
        }

        CharacterInfoDto first = characterInfos.get(0);
        CharacterInfoDto second = characterInfos.get(1);
        CharacterInfoDto third = characterInfos.get(2);

        List<String> mainRoles = List.of(
                safeRole(first.getDefaultPositionMain()),
                safeRole(second.getDefaultPositionMain()),
                safeRole(third.getDefaultPositionMain())
        );
        List<String> subRoles = List.of(
                safeRole(first.getDefaultPositionSub()),
                safeRole(second.getDefaultPositionSub()),
                safeRole(third.getDefaultPositionSub())
        );

        return new ModelPredictRequestDto(
                first.getCharacterNum(),
                second.getCharacterNum(),
                third.getCharacterNum(),
                safeWeaponCode(first),
                safeWeaponCode(second),
                safeWeaponCode(third),
                safeRole(first.getDefaultPositionMain()),
                safeRole(second.getDefaultPositionMain()),
                safeRole(third.getDefaultPositionMain()),
                safeRole(first.getDefaultPositionSub()),
                safeRole(second.getDefaultPositionSub()),
                safeRole(third.getDefaultPositionSub()),
                countRole(mainRoles, "melee"),
                countRole(mainRoles, "ranged"),
                countRole(mainRoles, "support"),
                countRole(subRoles, "bruiser"),
                countRole(subRoles, "assassin"),
                countRole(subRoles, "poke"),
                countRole(subRoles, "sustain"),
                countRole(subRoles, "util"),
                countRole(subRoles, "tank"),
                countRole(subRoles, "nuker")
        );
    }

    private int countRole(List<String> roles, String targetRole) {
        return (int) roles.stream()
                .filter(targetRole::equals)
                .count();
    }

    private int safeWeaponCode(CharacterInfoDto characterInfo) {
        return characterInfo.getWeaponCode() == null ? 0 : characterInfo.getWeaponCode();
    }

    private String safeRole(String role) {
        return role == null || role.isBlank() ? "unknown" : role.trim().toLowerCase();
    }

    private List<Integer> parseCharacterNums(List<String> characterCodes) {
        if (characterCodes == null || characterCodes.isEmpty()) {
            return List.of();
        }

        return characterCodes.stream()
                .filter(characterCode -> characterCode != null && !characterCode.isBlank())
                .map(Integer::parseInt)
                .toList();
    }

    private void sleepBetweenRequests() {
        try {
            Thread.sleep(API_DELAY_MILLIS);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Request delay interrupted.", exception);
        }
    }
}
