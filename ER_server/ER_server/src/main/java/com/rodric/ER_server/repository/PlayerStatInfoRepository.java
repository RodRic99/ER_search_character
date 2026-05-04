package com.rodric.ER_server.repository;

import com.rodric.ER_server.entity.PlayerStatInfo;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PlayerStatInfoRepository extends JpaRepository<PlayerStatInfo, Long> {
}
