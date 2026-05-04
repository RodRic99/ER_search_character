import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/api/er")
public class ERPredictController {

    private static final String FASTAPI_URL = "http://127.0.0.1:8000/predict";

    private final HttpClient httpClient = HttpClient.newHttpClient();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @PostMapping(
        value = "/predict",
        consumes = MediaType.APPLICATION_JSON_VALUE,
        produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<Object> predict(@RequestBody PredictRequest request) {
        try {
            String requestJson = objectMapper.writeValueAsString(request);

            HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(FASTAPI_URL))
                .header("Content-Type", "application/json")
                .PUT(HttpRequest.BodyPublishers.ofString(requestJson))
                .build();

            HttpResponse<String> response = httpClient.send(
                httpRequest,
                HttpResponse.BodyHandlers.ofString()
            );

            if (response.statusCode() >= 400) {
                throw new ResponseStatusException(
                    HttpStatus.BAD_GATEWAY,
                    "FastAPI prediction server returned status " + response.statusCode() + ": " + response.body()
                );
            }

            Object responseBody = objectMapper.readValue(response.body(), Object.class);
            return ResponseEntity.ok(responseBody);
        } catch (JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "요청 JSON 직렬화에 실패했습니다.", e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "예측 서버 호출이 중단되었습니다.", e);
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "FastAPI 예측 서버 호출에 실패했습니다.", e);
        }
    }

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ErrorResponse> handleResponseStatusException(ResponseStatusException e) {
        return ResponseEntity
            .status(e.getStatusCode())
            .body(new ErrorResponse(e.getReason()));
    }

    public record PredictRequest(
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
    ) {}

    public record ErrorResponse(String message) {}
}
