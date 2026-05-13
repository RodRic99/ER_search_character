package com.rodric.ER_server.service;

import com.rodric.ER_server.dto.CharacterInfoDto;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

@Service
@RequiredArgsConstructor
public class CharacterMasterService {

    private static final Logger log = LoggerFactory.getLogger(CharacterMasterService.class);

    private final NamedParameterJdbcTemplate jdbcTemplate;

    public List<String> convertCharacterCodesToNames(List<String> characterCodes) {
        return findCharactersByCodes(characterCodes).stream()
                .map(CharacterInfoDto::getCharacterName)
                .toList();
    }

    public List<CharacterInfoDto> findCharactersByCodes(List<String> characterCodes) {
        if (characterCodes == null || characterCodes.isEmpty()) {
            return List.of();
        }

        List<Integer> characterNums = characterCodes.stream()
                .filter(characterCode -> characterCode != null && !characterCode.isBlank())
                .map(this::parseCharacterNum)
                .toList();

        if (characterNums.isEmpty()) {
            return List.of();
        }

        return findCharactersByNumsAndWeapons(
                characterNums,
                characterNums.stream().map(characterNum -> 0).toList()
        );
    }

    public List<CharacterInfoDto> findCharactersByNumsAndWeapons(List<Integer> characterNums, List<Integer> weaponCodes) {
        if (characterNums == null || weaponCodes == null || characterNums.isEmpty() || characterNums.size() != weaponCodes.size()) {
            return List.of();
        }

        List<Integer> sanitizedCharacterNums = characterNums.stream()
                .filter(Objects::nonNull)
                .toList();
        if (sanitizedCharacterNums.size() != characterNums.size()) {
            return List.of();
        }

        Map<Integer, CharacterInfoDto> baseCharacterMap = jdbcTemplate.query(
                        """
                        SELECT characterNum, characterName, default_position_main, default_position_sub
                        FROM character_master
                        WHERE characterNum IN (:characterNums)
                        """,
                        new MapSqlParameterSource("characterNums", sanitizedCharacterNums),
                        (resultSet, rowNum) -> Map.entry(
                                resultSet.getInt("characterNum"),
                                new CharacterInfoDto(
                                        resultSet.getInt("characterNum"),
                                        resultSet.getString("characterName"),
                                        resultSet.getString("default_position_main"),
                                        resultSet.getString("default_position_sub"),
                                        0
                                )
                        )
                )
                .stream()
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));

        Map<String, String> overrideSubPositionByCharacterAndWeapon = findOverrideSubPositionsByPairs(characterNums, weaponCodes);

        List<CharacterInfoDto> resolvedInfos = IntStream.range(0, characterNums.size())
                .mapToObj(index -> {
                    Integer characterNum = characterNums.get(index);
                    Integer weaponCode = weaponCodes.get(index);
                    CharacterInfoDto baseInfo = baseCharacterMap.get(characterNum);
                    if (baseInfo == null) {
                        return new CharacterInfoDto(characterNum, String.valueOf(characterNum), "unknown", "unknown", weaponCode);
                    }

                    String overrideSub = overrideSubPositionByCharacterAndWeapon.get(characterWeaponKey(characterNum, weaponCode));
                    String resolvedSub = overrideSub == null || overrideSub.isBlank()
                            ? baseInfo.getDefaultPositionSub()
                            : overrideSub;

                    return new CharacterInfoDto(
                            baseInfo.getCharacterNum(),
                            baseInfo.getCharacterName(),
                            baseInfo.getDefaultPositionMain(),
                            resolvedSub,
                            weaponCode == null ? 0 : weaponCode
                    );
                })
                .toList();

        log.info("Character mapping request nums={}, weaponCodes={}, foundCount={}",
                characterNums, weaponCodes, resolvedInfos.size());

        return resolvedInfos;
    }

    private Map<String, String> findOverrideSubPositionsByPairs(List<Integer> characterNums, List<Integer> weaponCodes) {
        List<String> characterWeaponKeys = IntStream.range(0, characterNums.size())
                .mapToObj(index -> characterWeaponKey(characterNums.get(index), weaponCodes.get(index)))
                .distinct()
                .toList();

        if (characterWeaponKeys.isEmpty()) {
            return Map.of();
        }

        try {
            return jdbcTemplate.query(
                            """
                            SELECT characterNum, weaponCode, override_position_sub
                            FROM character_weapon_role
                            WHERE CONCAT(characterNum, ':', weaponCode) IN (:characterWeaponKeys)
                            """,
                            new MapSqlParameterSource("characterWeaponKeys", characterWeaponKeys),
                            (resultSet, rowNum) -> Map.entry(
                                    characterWeaponKey(resultSet.getInt("characterNum"), resultSet.getInt("weaponCode")),
                                    resultSet.getString("override_position_sub")
                            )
                    )
                    .stream()
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
        } catch (DataAccessException exception) {
            log.warn("Failed to load character weapon role overrides by explicit pairs.", exception);
            return new HashMap<>();
        }
    }

    private String characterWeaponKey(Integer characterNum, Integer weaponCode) {
        return characterNum + ":" + (weaponCode == null ? 0 : weaponCode);
    }

    private Integer parseCharacterNum(String characterCode) {
        try {
            return Integer.parseInt(characterCode);
        } catch (NumberFormatException exception) {
            throw new IllegalArgumentException("Invalid character code: " + characterCode, exception);
        }
    }
}
