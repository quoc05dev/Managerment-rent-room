package com.cntt.rentalmanagement.repository;

import com.cntt.rentalmanagement.domain.enums.RoomStatus;
import com.cntt.rentalmanagement.domain.models.Room;
import com.cntt.rentalmanagement.domain.models.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;


public interface RoomRepository extends JpaRepository<Room, Long>, RoomRepositoryCustom{
    long countAllByUser(User user);

    long count();
    long countAllByStatusAndUser(RoomStatus status, User user);

    Room[] findByUser(User user);

    long countByIsApprove(Boolean isApprove);
}
