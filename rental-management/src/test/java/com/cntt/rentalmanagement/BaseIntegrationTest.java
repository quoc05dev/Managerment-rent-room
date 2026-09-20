package com.cntt.rentalmanagement;

import com.cntt.rentalmanagement.domain.enums.AuthProvider;
import com.cntt.rentalmanagement.domain.enums.RoleName;
import com.cntt.rentalmanagement.domain.models.Role;
import com.cntt.rentalmanagement.domain.models.User;
import com.cntt.rentalmanagement.repository.RoleRepository;
import com.cntt.rentalmanagement.repository.UserRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import javax.annotation.PostConstruct;
import java.util.HashSet;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
public abstract class BaseIntegrationTest {

    @Autowired
    protected MockMvc mockMvc;

    @Autowired
    protected ObjectMapper objectMapper;

    @Autowired
    protected UserRepository userRepository;

    @Autowired
    protected RoleRepository roleRepository;

    @Autowired
    protected PasswordEncoder passwordEncoder;

    protected User testUser;
    protected User testRentaler;
    protected String userToken;
    protected String rentalerToken;

    @PostConstruct
    void setupTestData() {
        Role userRole = roleRepository.findByName(RoleName.ROLE_USER)
                .orElseGet(() -> roleRepository.save(new Role(RoleName.ROLE_USER)));
        Role rentalerRole = roleRepository.findByName(RoleName.ROLE_RENTALER)
                .orElseGet(() -> roleRepository.save(new Role(RoleName.ROLE_RENTALER)));

        testUser = new User();
        testUser.setName("Test User");
        testUser.setEmail("testuser@example.com");
        testUser.setPassword(passwordEncoder.encode("password123"));
        testUser.setProvider(AuthProvider.local);
        testUser.setEmailVerified(true);
        testUser.setIsConfirmed(true);
        testUser.setRoles(new HashSet<>() {{ add(userRole); }});
        testUser = userRepository.save(testUser);

        testRentaler = new User();
        testRentaler.setName("Test Rentaler");
        testRentaler.setEmail("testrentaler@example.com");
        testRentaler.setPassword(passwordEncoder.encode("password123"));
        testRentaler.setProvider(AuthProvider.local);
        testRentaler.setEmailVerified(true);
        testRentaler.setIsConfirmed(true);
        testRentaler.setRoles(new HashSet<>() {{ add(rentalerRole); }});
        testRentaler = userRepository.save(testRentaler);
    }
}
