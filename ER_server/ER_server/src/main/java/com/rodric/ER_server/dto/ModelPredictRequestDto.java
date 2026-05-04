package com.rodric.ER_server.dto;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.stream.Collectors;

public record ModelPredictRequestDto(
        int characterNum_1,
        int characterNum_2,
        int characterNum_3,
        int weaponCode_1,
        int weaponCode_2,
        int weaponCode_3,
        String position_main_1,
        String position_main_2,
        String position_main_3,
        String position_sub_1,
        String position_sub_2,
        String position_sub_3,
        int main_melee_cnt,
        int main_ranged_cnt,
        int main_support_cnt,
        int sub_bruiser_cnt,
        int sub_assassin_cnt,
        int sub_poke_cnt,
        int sub_sustain_cnt,
        int sub_util_cnt,
        int sub_tank_cnt,
        int sub_nuker_cnt
) {
    public Map<String, Object> toRequestBody() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("characterNum_1", characterNum_1);
        body.put("characterNum_2", characterNum_2);
        body.put("characterNum_3", characterNum_3);
        body.put("weaponCode_1", weaponCode_1);
        body.put("weaponCode_2", weaponCode_2);
        body.put("weaponCode_3", weaponCode_3);
        body.put("position_main_1", position_main_1);
        body.put("position_main_2", position_main_2);
        body.put("position_main_3", position_main_3);
        body.put("position_sub_1", position_sub_1);
        body.put("position_sub_2", position_sub_2);
        body.put("position_sub_3", position_sub_3);
        body.put("main_melee_cnt", main_melee_cnt);
        body.put("main_ranged_cnt", main_ranged_cnt);
        body.put("main_support_cnt", main_support_cnt);
        body.put("sub_bruiser_cnt", sub_bruiser_cnt);
        body.put("sub_assassin_cnt", sub_assassin_cnt);
        body.put("sub_poke_cnt", sub_poke_cnt);
        body.put("sub_sustain_cnt", sub_sustain_cnt);
        body.put("sub_util_cnt", sub_util_cnt);
        body.put("sub_tank_cnt", sub_tank_cnt);
        body.put("sub_nuker_cnt", sub_nuker_cnt);
        return body;
    }

    public String toJson() {
        return toRequestBody().entrySet().stream()
                .map(entry -> "\"" + entry.getKey() + "\":" + toJsonValue(entry.getValue()))
                .collect(Collectors.joining(",", "{", "}"));
    }

    private String toJsonValue(Object value) {
        if (value instanceof Number || value instanceof Boolean) {
            return value.toString();
        }

        return "\"" + escapeJson(String.valueOf(value)) + "\"";
    }

    private String escapeJson(String value) {
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"");
    }
}
