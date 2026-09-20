package com.cntt.rentalmanagement.controller;

import com.cntt.rentalmanagement.BaseIntegrationTest;
import com.cntt.rentalmanagement.domain.payload.request.LoginRequest;
import org.junit.jupiter.api.*;
import org.springframework.http.MediaType;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class RequestControllerTest extends BaseIntegrationTest {

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

    @Test @Order(1) @DisplayName("GET /request/customer - Danh sach yeu cau")
    void listCustomerRequests() throws Exception {
        mockMvc.perform(get("/request/customer")
                        .param("keyword", "").param("phone", "0912345678")
                        .param("pageNo", "1").param("pageSize", "10"))
                .andExpect(status().isOk());
    }

    @Test @Order(2) @DisplayName("POST /request - Gui yeu cau thue phong")
    void submitRentalRequest() throws Exception {
        String token = getAuthToken();
        String requestJson = "{\"roomId\": " + testRoom.getId() + ", \"phone\": \"0912345678\", \"nameOfRent\": \"Test User\"}";
        mockMvc.perform(post("/request").contentType(MediaType.APPLICATION_JSON).content(requestJson)
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test @Order(3) @DisplayName("GET /request - Danh sach yeu cau (rentaler)")
    void listRequests() throws Exception {
        LoginRequest req = new LoginRequest();
        req.setEmail("testrentaler@example.com");
        req.setPassword("password123");
        var result = mockMvc.perform(post("/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req))).andReturn();
        String token = objectMapper.readTree(result.getResponse().getContentAsString())
                .get("accessToken").asText();
        mockMvc.perform(get("/request").param("keyword", "").param("pageNo", "1").param("pageSize", "10")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test @Order(4) @DisplayName("GET /request/customer - Khong can xac thuc")
    void customerRequestsNoAuth() throws Exception {
        mockMvc.perform(get("/request/customer")
                        .param("keyword", "").param("phone", "0912345678")
                        .param("pageNo", "1").param("pageSize", "10"))
                .andExpect(status().isOk());
    }
}
