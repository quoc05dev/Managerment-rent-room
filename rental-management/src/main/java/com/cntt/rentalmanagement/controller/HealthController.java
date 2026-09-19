package com.cntt.rentalmanagement.controller;

import com.cntt.rentalmanagement.repository.UserRepository;
import com.cntt.rentalmanagement.repository.RoleRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.util.HashMap;
import java.util.Map;

@RestController
public class HealthController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private DataSource dataSource;

    @GetMapping("/health")
    public Map<String, Object> health() {
        Map<String, Object> result = new HashMap<>();
        result.put("status", "UP");

        try {
            Connection conn = dataSource.getConnection();
            result.put("database", "CONNECTED");
            result.put("databaseUrl", conn.getMetaData().getURL());
            conn.close();
        } catch (Exception e) {
            result.put("database", "ERROR");
            result.put("databaseError", e.getMessage());
        }

        try {
            result.put("totalUsers", userRepository.count());
        } catch (Exception e) {
            result.put("userCountError", e.getMessage());
        }

        try {
            result.put("totalRoles", roleRepository.count());
        } catch (Exception e) {
            result.put("roleCountError", e.getMessage());
        }

        return result;
    }
}
