package com.rodric.ER_server.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Map;

@Getter
@Setter
public class PlayerMost3ItemDto {

    // 플레이어 1명의 닉네임, userId, 모스트3 캐릭터 이름 목록.
    private String playerName;
    private String userId;
    private Integer rankPoint;
    private List<String> most3Characters;
    private List<Integer> most3CharacterNums;

    // 예전 실시간 모델 응답과 호환하기 위해 남겨둔 필드.
    private Map<String, Object> prediction;

    public PlayerMost3ItemDto() {
    }

    public PlayerMost3ItemDto(String playerName, String userId, List<String> most3Characters) {
        this.playerName = playerName;
        this.userId = userId;
        this.most3Characters = most3Characters;
    }

    public PlayerMost3ItemDto(String playerName, String userId, List<String> most3Characters, List<Integer> most3CharacterNums) {
        this.playerName = playerName;
        this.userId = userId;
        this.most3Characters = most3Characters;
        this.most3CharacterNums = most3CharacterNums;
    }

    public PlayerMost3ItemDto(String playerName, String userId, Integer rankPoint, List<String> most3Characters, List<Integer> most3CharacterNums) {
        this.playerName = playerName;
        this.userId = userId;
        this.rankPoint = rankPoint;
        this.most3Characters = most3Characters;
        this.most3CharacterNums = most3CharacterNums;
    }

    public PlayerMost3ItemDto(String playerName, String userId, List<String> most3Characters, Map<String, Object> prediction) {
        this.playerName = playerName;
        this.userId = userId;
        this.most3Characters = most3Characters;
        this.prediction = prediction;
    }
}
