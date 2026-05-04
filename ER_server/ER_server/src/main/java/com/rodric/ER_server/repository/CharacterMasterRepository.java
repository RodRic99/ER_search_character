package com.rodric.ER_server.repository;

import com.rodric.ER_server.entity.CharacterMaster;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;

public interface CharacterMasterRepository extends JpaRepository<CharacterMaster, Integer> {

    List<CharacterMaster> findByCharacterNumIn(Collection<Integer> characterNums);
}
