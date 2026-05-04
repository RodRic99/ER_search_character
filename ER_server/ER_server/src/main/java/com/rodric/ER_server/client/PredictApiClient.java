package com.rodric.ER_server.client;

import com.rodric.ER_server.dto.ModelPredictRequestDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Map;

@Component
public class PredictApiClient {

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final URI predictUri;

    public PredictApiClient(@Value("${predict-api.base-url:http://127.0.0.1:8000}") String baseUrl) {
        this.httpClient = HttpClient.newHttpClient();
        this.objectMapper = new ObjectMapper();
        this.predictUri = URI.create(trimTrailingSlash(baseUrl) + "/predict");
    }

    public Map<String, Object> predict(ModelPredictRequestDto requestDto) {
        String requestBody = requestDto.toJson();
        HttpRequest request = HttpRequest.newBuilder(predictUri)
                .version(HttpClient.Version.HTTP_1_1)
                .header("Content-Type", "application/json; charset=utf-8")
                .header("Accept", "application/json")
                .PUT(HttpRequest.BodyPublishers.ofString(requestBody, StandardCharsets.UTF_8))
                .build();

        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new IllegalStateException("Predict API failed: " + response.statusCode() + " " + response.body());
            }

            return objectMapper.readValue(response.body(), Map.class);
        } catch (IOException exception) {
            throw new IllegalStateException("Predict API request failed.", exception);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Predict API request interrupted.", exception);
        }
    }

    private String trimTrailingSlash(String value) {
        if (value.endsWith("/")) {
            return value.substring(0, value.length() - 1);
        }

        return value;
    }
}
