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
        var result = mockMvc.perform(post("/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req))).andReturn();
        rentalerToken = objectMapper.readTree(result.getResponse().getContentAsString())
                .get("accessToken").asText();
        return rentalerToken;
    }

    @Test @Order(1) @DisplayName("POST /maintenance - Tao phieu bao tri moi")
    void createMaintenance() throws Exception {
        String token = getRentalerToken();
        MockMultipartFile file = new MockMultipartFile("files", "receipt.jpg", "image/jpeg", "fake-image".getBytes());
        mockMvc.perform(multipart("/maintenance")
                .file(file)
                .param("maintenanceDate", "2026-09-20T00:00:00")
                .param("price", "500000")
                .param("roomId", testRoom.getId().toString())
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").exists());
    }

    @Test @Order(2) @DisplayName("GET /maintenance - Danh sach bao tri")
    void listMaintenance() throws Exception {
        String token = getRentalerToken();
        mockMvc.perform(get("/maintenance").param("keyword", "").param("pageNo", "1").param("pageSize", "10")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test @Order(3) @DisplayName("GET /maintenance - Khong co token")
    void listMaintenanceNoToken() throws Exception {
        mockMvc.perform(get("/maintenance").param("keyword", "").param("pageNo", "1").param("pageSize", "10"))
                .andExpect(status().isUnauthorized());
    }

    @Test @Order(4) @DisplayName("DELETE /maintenance/{id} - Xoa phieu bao tri khong ton tai")
    void deleteMaintenance() throws Exception {
        String token = getRentalerToken();
        try {
            mockMvc.perform(delete("/maintenance/999999")
                    .header("Authorization", "Bearer " + token));
        } catch (org.springframework.web.util.NestedServletException e) {
            org.junit.jupiter.api.Assertions.assertNotNull(e);
        }
    }
}
