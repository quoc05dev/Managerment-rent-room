package com.cntt.rentalmanagement.controller;

import com.cntt.rentalmanagement.BaseIntegrationTest;
import com.cntt.rentalmanagement.domain.payload.request.LoginRequest;
import org.junit.jupiter.api.*;
import org.springframework.http.MediaType;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class UserControllerTest extends BaseIntegrationTest {

    private String getAuthToken() throws Exception {
        if (userToken != null) return userToken;
        LoginRequest req = new LoginRequest();
        req.setEmail("testuser@example.com");
        req.setPassword("password123");
        var result = mockMvc.perform(post("/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req))).andReturn();
        userToken = objectMapper.readTree(result.getResponse().getContentAsString())
                .get("accessToken").asText();
        return userToken;
    }

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

    @Test @Order(1) @DisplayName("GET /user/me - Xem thong tin ca nhan (USER)")
    void getCurrentUser() throws Exception {
        String token = getAuthToken();
        mockMvc.perform(get("/user/me").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("testuser@example.com"))
                .andExpect(jsonPath("$.name").value("Test User"));
    }

    @Test @Order(2) @DisplayName("GET /rentaler/me - Xem thong tin ca nhan (RENTALER)")
    void getCurrentRentaler() throws Exception {
        String token = getRentalerToken();
        mockMvc.perform(get("/rentaler/me").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("testrentaler@example.com"));
    }

    @Test @Order(3) @DisplayName("GET /user/me - Khong co token")
    void getCurrentUserNoToken() throws Exception {
        mockMvc.perform(get("/user/me")).andExpect(status().isUnauthorized());
    }

    @Test @Order(4) @DisplayName("GET /user/me - Token khong hop le")
    void getCurrentUserInvalidToken() throws Exception {
        mockMvc.perform(get("/user/me").header("Authorization", "Bearer invalid.token.here"))
                .andExpect(status().isUnauthorized());
    }

    @Test @Order(5) @DisplayName("PUT /user/update - Cap nhat thong tin nguoi dung")
    void updateUser() throws Exception {
        String token = getAuthToken();
        String userJson = objectMapper.writeValueAsString(testUser);
        mockMvc.perform(put("/user/update").contentType(MediaType.APPLICATION_JSON)
                .content(userJson).header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test @Order(6) @DisplayName("GET /account/customer - Danh sach khach hang")
    void getCustomerAccounts() throws Exception {
        mockMvc.perform(get("/account/customer").param("pageNo", "1").param("pageSize", "10"))
                .andExpect(status().isOk());
    }

    @Test @Order(7) @DisplayName("GET /account/{id} - Xem thong tin tai khoan")
    void getAccountById() throws Exception {
        mockMvc.perform(get("/account/" + testUser.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("testuser@example.com"));
    }
}
