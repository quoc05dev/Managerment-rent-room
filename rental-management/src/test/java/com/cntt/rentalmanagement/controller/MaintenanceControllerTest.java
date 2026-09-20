package com.cntt.rentalmanagement.controller;

import com.cntt.rentalmanagement.BaseIntegrationTest;
import com.cntt.rentalmanagement.domain.payload.request.LoginRequest;
import org.junit.jupiter.api.*;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class MaintenanceControllerTest extends BaseIntegrationTest {

    private String getRentalerToken() throws Exception {
        if (rentalerToken != null) return rentalerToken;
        LoginRequest req = new LoginRequest();
        req.setEmail("testrentaler@example.com");
        req.setPassword("password123");
        var result = mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andReturn();
        rentalerToken = objectMapper.readTree(result.getResponse().getContentAsString())
                .get("accessToken").asText();
        return rentalerToken;
    }

    @Test
    @Order(1)
    @DisplayName("POST /maintenance - Tao phieu bao tri moi")
    void createMaintenance() throws Exception {
        String token = getRentalerToken();
        MockMultipartFile date = new MockMultipartFile("maintenanceDate", "", "text/plain", "2026-09-20".getBytes());
        MockMultipartFile price = new MockMultipartFile("price", "", "text/plain", "500000".getBytes());
        MockMultipartFile roomId = new MockMultipartFile("roomId", "", "text/plain", "1".getBytes());
        MockMultipartFile file = new MockMultipartFile("files", "receipt.jpg", "image/jpeg", "fake-image".getBytes());

        mockMvc.perform(multipart("/maintenance")
                        .file(date).file(price).file(roomId).file(file)
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").exists());
    }

    @Test
    @Order(2)
    @DisplayName("GET /maintenance - Danh sach bao tri")
    void listMaintenance() throws Exception {
        String token = getRentalerToken();

        mockMvc.perform(get("/maintenance")
                        .param("keyword", "")
                        .param("pageNo", "1")
                        .param("pageSize", "10")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }

    @Test
    @Order(3)
    @DisplayName("GET /maintenance - Khong co token")
    void listMaintenanceNoToken() throws Exception {
        mockMvc.perform(get("/maintenance")
                        .param("keyword", "")
                        .param("pageNo", "1")
                        .param("pageSize", "10"))
                .andExpect(status().isForbidden());
    }

    @Test
    @Order(4)
    @DisplayName("DELETE /maintenance/{id} - Xoa phieu bao tri")
    void deleteMaintenance() throws Exception {
        String token = getRentalerToken();

        mockMvc.perform(delete("/maintenance/1")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }
}
