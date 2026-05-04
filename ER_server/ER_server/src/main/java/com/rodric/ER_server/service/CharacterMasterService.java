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
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CharacterMasterService {

    private static final Logger log = LoggerFactory.getLogger(CharacterMasterService.class);

    private final NamedParameterJdbcTemplate jdbcTemplate;

    // 외부 API의 캐릭터 번호를 프론트에 보여줄 캐릭터 이름으로 변환한다.
    public List<String> convertCharacterCodesToNames(List<String> characterCodes) {
        return findCharactersByCodes(characterCodes).stream()
                .map(CharacterInfoDto::getCharacterName)
                .toList();
    }

    // 캐릭터 표시 정보와 모델 조합 조회에 필요한 부가 정보를 함께 가져온다.
    // character_master: 캐릭터 이름, 기본 포지션
    // rankdb_train_base: 캐릭터별 대표 무기
    // character_weapon_role: 캐릭터 + 무기 조합에 따른 서브 포지션 보정값
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

        MapSqlParameterSource params = new MapSqlParameterSource("characterNums", characterNums);
        Map<Integer, Integer> representativeWeaponByCharacter = findRepresentativeWeaponCodes(characterNums);
        Map<String, String> overrideSubPositionByCharacterAndWeapon =
                findOverrideSubPositions(representativeWeaponByCharacter);

        Map<Integer, CharacterInfoDto> characterByNum = jdbcTemplate.query(
                        """
                        SELECT characterNum, characterName, default_position_main, default_position_sub
                        FROM character_master
                        WHERE characterNum IN (:characterNums)
                        """,
                        params,
                        (resultSet, rowNum) -> Map.entry(
                                resultSet.getInt("characterNum"),
                                buildCharacterInfoDto(
                                        resultSet.getInt("characterNum"),
                                        resultSet.getString("characterName"),
                                        resultSet.getString("default_position_main"),
                                        resultSet.getString("default_position_sub"),
                                        representativeWeaponByCharacter,
                                        overrideSubPositionByCharacterAndWeapon
                                )
                        )
                )
                .stream()
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));

        log.info("Character mapping request codes={}, foundCount={}, result={}",
                characterNums, characterByNum.size(), characterByNum);

        return characterNums.stream()
                .map(characterNum -> characterByNum.getOrDefault(
                        characterNum,
                        new CharacterInfoDto(characterNum, String.valueOf(characterNum), "unknown", "unknown")
                ))
                .toList();
    }

    private CharacterInfoDto buildCharacterInfoDto(
            Integer characterNum,
            String characterName,
            String defaultPositionMain,
            String defaultPositionSub,
            Map<Integer, Integer> representativeWeaponByCharacter,
            Map<String, String> overrideSubPositionByCharacterAndWeapon
    ) {
        Integer weaponCode = representativeWeaponByCharacter.getOrDefault(characterNum, 0);
        String overridePositionSub = overrideSubPositionByCharacterAndWeapon.get(characterWeaponKey(characterNum, weaponCode));
        String positionSub = overridePositionSub == null || overridePositionSub.isBlank()
                ? defaultPositionSub
                : overridePositionSub;

        return new CharacterInfoDto(characterNum, characterName, defaultPositionMain, positionSub, weaponCode);
    }

    // 학습 데이터에서 가장 많이 사용된 무기를 해당 캐릭터의 대표 무기로 선택한다.
    // 배치 모델이 조합표를 만들 때 쓰는 기준과 백엔드 조회 기준을 맞추기 위함이다.
    private Map<Integer, Integer> findRepresentativeWeaponCodes(List<Integer> characterNums) {
        Map<Integer, Integer> representativeWeaponByCharacter = new HashMap<>();

        try {
            jdbcTemplate.query(
                    """
                    SELECT characterNum, weaponCode, COUNT(*) AS weaponCount
                    FROM (
                        SELECT characterNum_1 AS characterNum, weaponCode_1 AS weaponCode FROM rankdb_train_base
                        UNION ALL
                        SELECT characterNum_2 AS characterNum, weaponCode_2 AS weaponCode FROM rankdb_train_base
                        UNION ALL
                        SELECT characterNum_3 AS characterNum, weaponCode_3 AS weaponCode FROM rankdb_train_base
                    ) weapon_stats
                    WHERE characterNum IN (:characterNums)
                      AND weaponCode IS NOT NULL
                    GROUP BY characterNum, weaponCode
                    ORDER BY characterNum ASC, weaponCount DESC, weaponCode ASC
                    """,
                    new MapSqlParameterSource("characterNums", characterNums),
                    resultSet -> {
                        int characterNum = resultSet.getInt("characterNum");
                        representativeWeaponByCharacter.putIfAbsent(characterNum, resultSet.getInt("weaponCode"));
                    }
            );
        } catch (DataAccessException exception) {
            log.warn("Failed to load representative weapon codes from rankdb_train_base. Falling back to character_weapon_role.", exception);
        }

        representativeWeaponByCharacter.putAll(findFallbackWeaponCodes(characterNums, representativeWeaponByCharacter));
        return representativeWeaponByCharacter;
    }

    // 학습 데이터에서 대표 무기를 찾지 못하면 character_weapon_role에 등록된 무기 중 하나를 대체값으로 사용한다.
    private Map<Integer, Integer> findFallbackWeaponCodes(
            List<Integer> characterNums,
            Map<Integer, Integer> representativeWeaponByCharacter
    ) {
        List<Integer> missingCharacterNums = characterNums.stream()
                .filter(characterNum -> !representativeWeaponByCharacter.containsKey(characterNum))
                .toList();

        if (missingCharacterNums.isEmpty()) {
            return Map.of();
        }

        try {
            return jdbcTemplate.query(
                            """
                            SELECT characterNum, MIN(weaponCode) AS weaponCode
                            FROM character_weapon_role
                            WHERE characterNum IN (:characterNums)
                            GROUP BY characterNum
                            """,
                            new MapSqlParameterSource("characterNums", missingCharacterNums),
                            (resultSet, rowNum) -> Map.entry(
                                    resultSet.getInt("characterNum"),
                                    resultSet.getInt("weaponCode")
                            )
                    )
                    .stream()
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
        } catch (DataAccessException exception) {
            log.warn("Failed to load fallback weapon codes from character_weapon_role.", exception);
            return Map.of();
        }
    }

    // characterNum + weaponCode가 정확히 일치하는 경우에만 서브 포지션 보정값을 적용한다.
    private Map<String, String> findOverrideSubPositions(Map<Integer, Integer> representativeWeaponByCharacter) {
        List<String> characterWeaponKeys = representativeWeaponByCharacter.entrySet().stream()
                .filter(entry -> entry.getValue() != null && entry.getValue() != 0)
                .map(entry -> characterWeaponKey(entry.getKey(), entry.getValue()))
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
            log.warn("Failed to load character weapon role overrides.", exception);
            return Map.of();
        }
    }

    private String characterWeaponKey(Integer characterNum, Integer weaponCode) {
        return characterNum + ":" + weaponCode;
    }

    private Integer parseCharacterNum(String characterCode) {
        try {
            return Integer.parseInt(characterCode);
        } catch (NumberFormatException exception) {
            throw new IllegalArgumentException("Invalid character code: " + characterCode, exception);
        }
    }
}
