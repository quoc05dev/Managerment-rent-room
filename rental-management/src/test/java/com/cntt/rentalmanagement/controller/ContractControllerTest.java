package com.cntt.rentalmanagement.controller;

import com.cntt.rentalmanagement.BaseIntegrationTest;
import com.cntt.rentalmanagement.domain.payload.request.LoginRequest;
import org.junit.jupiter.api.*;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class ContractControllerTest extends BaseIntegrationTest {

    private String getAuthToken() throws Exception {
        if (userToken != null) return userToken;
        LoginRequest req = new LoginRequest();
        req.setEmail("testrentaler@example.com");
        req.setPassword("password123");
        var result = mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andReturn();
        userToken = objectMapper.readTree(result.getResponse().getContentAsString())
                .get("accessToken").asText();
        return userToken;
    }

    @Test
    @Order(1)
    @DisplayName("GET /contract - Danh sach hop dong (rentaler)")
    void listContracts() throws Exception {
        String token = getAuthToken();

        mockMvc.perform(get("/contract")
                        .param("pageNo", "1")
                        .param("pageSize", "10")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }

    @Test
    @Order(2)
    @DisplayName("GET /contract/customer - Danh sach hop dong (customer)")
    void listCustomerContracts() throws Exception {
        String token = getAuthToken();

        mockMvc.perform(get("/contract/customer")
                        .param("pageNo", "1")
                        .param("pageSize", "10")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }

    @Test
    @Order(3)
    @DisplayName("POST /contract - Tao hop dong moi")
    void createContract() throws Exception {
        String token = getAuthToken();
        MockMultipartFile name = new MockMultipartFile("name", "", "text/plain", "Hop dong test".getBytes());
        MockMultipartFile roomId = new MockMultipartFile("roomId", "", "text/plain", "1".getBytes());
        MockMultipartFile nameOfRent = new MockMultipartFile("nameOfRent", "", "text/plain", "Nguyen Van A".getBytes());
        MockMultipartFile numOfPeople = new MockMultipartFile("numOfPeople", "", "text/plain", "2".getBytes());
        MockMultipartFile phone = new MockMultipartFile("phone", "", "text/plain", "0912345678".getBytes());
        MockMultipartFile deadline = new MockMultipartFile("deadlineContract", "", "text/plain", "2027-12-31".getBytes());
        MockMultipartFile file = new MockMultipartFile("files", "contract.pdf", "application/pdf", "fake-pdf".getBytes());

        mockMvc.perform(multipart("/contract")
                        .file(name).file(roomId).file(nameOfRent)
                        .file(numOfPeople).file(phone).file(deadline).file(file)
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").exists());
    }

    @Test
    @Order(4)
    @DisplayName("GET /contract/{id} - Xem chi tiet hop dong")
    void getContractById() throws Exception {
        String token = getAuthToken();

        mockMvc.perform(get("/contract/1")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test
    @Order(5)
    @DisplayName("GET /contract - Khong co token")
    void listContractsNoToken() throws Exception {
        mockMvc.perform(get("/contract")
                        .param("pageNo", "1")
                        .param("pageSize", "10"))
                .andExpect(status().isForbidden());
    }
}
