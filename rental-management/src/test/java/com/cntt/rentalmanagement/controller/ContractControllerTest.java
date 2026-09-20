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

    @Test @Order(1) @DisplayName("GET /contract - Danh sach hop dong (rentaler)")
    void listContracts() throws Exception {
        String token = getAuthToken();
        mockMvc.perform(get("/contract").param("pageNo", "1").param("pageSize", "10")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test @Order(2) @DisplayName("GET /contract/customer - Danh sach hop dong (customer)")
    void listCustomerContracts() throws Exception {
        String token = getAuthToken();
        mockMvc.perform(get("/contract/customer").param("phone", "0987654321").param("pageNo", "1").param("pageSize", "10")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test @Order(3) @DisplayName("POST /contract - Tao hop dong moi")
    void createContract() throws Exception {
        String token = getAuthToken();
        MockMultipartFile file = new MockMultipartFile("files", "contract.pdf", "application/pdf", "fake-pdf".getBytes());
        mockMvc.perform(multipart("/contract")
                .file(file)
                .param("name", "Hop dong test")
                .param("roomId", testRoom.getId().toString())
                .param("nameOfRent", "Nguyen Van A")
                .param("numOfPeople", "2")
                .param("phone", "0912345678")
                .param("deadlineContract", "2027-12-31T00:00:00")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").exists());
    }

    @Test @Order(4) @DisplayName("GET /contract/{id} - Hop dong khong ton tai")
    void getContractById() throws Exception {
        String token = getAuthToken();
        mockMvc.perform(get("/contract/999999")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest());
    }

    @Test @Order(5) @DisplayName("GET /contract - Khong co token")
    void listContractsNoToken() throws Exception {
        mockMvc.perform(get("/contract").param("pageNo", "1").param("pageSize", "10"))
                .andExpect(status().isUnauthorized());
    }
}
