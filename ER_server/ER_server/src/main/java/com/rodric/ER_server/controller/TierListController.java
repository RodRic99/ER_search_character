package com.rodric.ER_server.controller;

import com.rodric.ER_server.dto.TierListResponseDto;
import com.rodric.ER_server.service.TierListService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/tier-list")
@RequiredArgsConstructor
public class TierListController {

    private final TierListService tierListService;

    @GetMapping
    public TierListResponseDto getTierList(
            @RequestParam(name = "rankTier", defaultValue = "diamond") String rankTier,
            @RequestParam(name = "week", defaultValue = "1") int week
    ) {
        return tierListService.getTierList(rankTier, week);
    }
}
