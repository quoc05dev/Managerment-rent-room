package com.cntt.rentalmanagement.controller;

import com.cntt.rentalmanagement.BaseIntegrationTest;
import com.cntt.rentalmanagement.domain.payload.request.LoginRequest;
import org.junit.jupiter.api.*;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class RoomControllerTest extends BaseIntegrationTest {

    private String getAuthToken() throws Exception {
        if (userToken != null) return userToken;
        LoginRequest req = new LoginRequest();
        req.setEmail("testuser@example.com");
        req.setPassword("password123");
        var result = mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andReturn();
        userToken = objectMapper.readTree(result.getResponse().getContentAsString())
                .get("accessToken").asText();
        return userToken;
    }

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
    @DisplayName("POST /room - Tao phong moi (rentaler)")
    void createRoomSuccess() throws Exception {
        String token = getRentalerToken();
        MockMultipartFile title = new MockMultipartFile("title", "", "text/plain",
                "Phong tro test".getBytes());
        MockMultipartFile desc = new MockMultipartFile("description", "", "text/plain",
                "Mo ta phong tro test".getBytes());
        MockMultipartFile price = new MockMultipartFile("price", "", "text/plain",
                "2000000".getBytes());
        MockMultipartFile lat = new MockMultipartFile("latitude", "", "text/plain",
                "21.0285".getBytes());
        MockMultipartFile lng = new MockMultipartFile("longitude", "", "text/plain",
                "105.8542".getBytes());
        MockMultipartFile addr = new MockMultipartFile("address", "", "text/plain",
                "123 Test Street".getBytes());
        MockMultipartFile locId = new MockMultipartFile("locationId", "", "text/plain",
                "1".getBytes());
        MockMultipartFile catId = new MockMultipartFile("categoryId", "", "text/plain",
                "2".getBytes());
        MockMultipartFile asset = new MockMultipartFile("asset", "", "text/plain",
                "0".getBytes());
        MockMultipartFile file = new MockMultipartFile("files", "test.jpg",
                "image/jpeg", "fake-image-data".getBytes());

        mockMvc.perform(multipart("/room/")
                        .file(title).file(desc).file(price)
                        .file(lat).file(lng).file(addr)
                        .file(locId).file(catId).file(asset).file(file)
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").exists());
    }

    @Test
    @Order(2)
    @DisplayName("GET /room/rent-home - Xem danh sach phong (public)")
    void getRentHomeSuccess() throws Exception {
        mockMvc.perform(get("/room/rent-home"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }

    @Test
    @Order(3)
    @DisplayName("GET /customer/room - Khach hang xem danh sach phong")
    void getCustomerRooms() throws Exception {
        mockMvc.perform(get("/customer/room")
                        .param("pageNo", "1")
                        .param("pageSize", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.totalElements").isNumber());
    }

    @Test
    @Order(4)
    @DisplayName("GET /customer/room - Tim kiem theo ten")
    void searchRoomsByTitle() throws Exception {
        mockMvc.perform(get("/customer/room")
                        .param("pageNo", "1")
                        .param("pageSize", "10")
                        .param("title", "Phong tro"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }

    @Test
    @Order(5)
    @DisplayName("GET /customer/room - Loc theo danh muc")
    void filterRoomsByCategory() throws Exception {
        mockMvc.perform(get("/customer/room")
                        .param("pageNo", "1")
                        .param("pageSize", "10")
                        .param("categoryId", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }

    @Test
    @Order(6)
    @DisplayName("POST /room/{id}/approve - Duyet phong")
    void approveRoom() throws Exception {
        String token = getRentalerToken();

        mockMvc.perform(post("/room/1/approve")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").exists());
    }

    @Test
    @Order(7)
    @DisplayName("GET /room/{id} - Xem chi tiet phong")
    void getRoomById() throws Exception {
        mockMvc.perform(get("/room/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.title").exists());
    }

    @Test
    @Order(8)
    @DisplayName("POST /room/{id}/comments - Them binh luan")
    void addComment() throws Exception {
        String token = getAuthToken();
        String commentJson = "{\"rateRating\": 5, \"content\": \"Phong dep lam!\"}";

        mockMvc.perform(post("/room/1/comments")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(commentJson)
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test
    @Order(9)
    @DisplayName("GET /room/{roomId}/comments - Xem binh luan")
    void getComments() throws Exception {
        mockMvc.perform(get("/room/1/comments"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }

    @Test
    @Order(10)
    @DisplayName("DELETE /room/{id} - Xoa phong (khong co quyen)")
    void deleteRoomUnauthorized() throws Exception {
        String token = getAuthToken();

        mockMvc.perform(delete("/room/1")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isForbidden());
    }
}
