package com.rodric.ER_server.controller;

import com.rodric.ER_server.dto.PlayerMost3RequestDto;
import com.rodric.ER_server.dto.PlayerMost3ResponseDto;
import com.rodric.ER_server.dto.SimulatorRecommendRequestDto;
import com.rodric.ER_server.dto.SimulatorRecommendResponseDto;
import com.rodric.ER_server.service.PlayerStatInfoService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/player-stats")
@RequiredArgsConstructor
public class PlayerStatInfoController {

    private static final Logger log = LoggerFactory.getLogger(PlayerStatInfoController.class);

    private final PlayerStatInfoService playerStatInfoService;

    @PostMapping("/most3")
    public PlayerMost3ResponseDto getPlayersMost3(@RequestBody PlayerMost3RequestDto requestDto) {
        return playerStatInfoService.getMost3ForPlayers(requestDto.getPlayerNames());
    }

    @PostMapping("/simulate")
    public SimulatorRecommendResponseDto simulate(@RequestBody SimulatorRecommendRequestDto requestDto) {
        return playerStatInfoService.recommendForSimulator(requestDto.getCharacterPools());
    }

    @ExceptionHandler(Exception.class)
    public void handleException(Exception exception) {
        log.error("Unhandled player stats request error", exception);
        throw new ResponseStatusException(
                HttpStatus.INTERNAL_SERVER_ERROR,
                "An internal server error occurred.",
                exception
        );
    }
}
