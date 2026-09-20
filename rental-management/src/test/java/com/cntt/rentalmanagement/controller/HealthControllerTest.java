package com.cntt.rentalmanagement.controller;

import com.cntt.rentalmanagement.BaseIntegrationTest;
import org.junit.jupiter.api.*;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class HealthControllerTest extends BaseIntegrationTest {

    @Test
    @DisplayName("GET /health - Kiem tra tinh trang he thong")
    void healthCheck() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.database").value("CONNECTED"))
                .andExpect(jsonPath("$.totalRoles").value(3))
                .andExpect(jsonPath("$.totalUsers").isNumber());
    }

    @Test
    @DisplayName("GET /health - Khong can xac thuc")
    void healthNoAuthRequired() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("GET /health - Co database URL")
    void healthHasDatabaseUrl() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.databaseUrl").isNotEmpty());
    }
}
