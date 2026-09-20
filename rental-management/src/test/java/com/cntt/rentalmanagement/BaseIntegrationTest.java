package com.cntt.rentalmanagement;

import com.cntt.rentalmanagement.domain.enums.AuthProvider;
import com.cntt.rentalmanagement.domain.enums.LockedStatus;
import com.cntt.rentalmanagement.domain.enums.RoleName;
import com.cntt.rentalmanagement.domain.enums.RoomStatus;
import com.cntt.rentalmanagement.domain.models.*;
import com.cntt.rentalmanagement.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import javax.annotation.PostConstruct;
import java.math.BigDecimal;
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

    @Autowired
    protected CategoryRepository categoryRepository;

    @Autowired
    protected LocationRepository locationRepository;

    @Autowired
    protected RoomRepository roomRepository;

    protected User testUser;
    protected User testRentaler;
    protected String userToken;
    protected String rentalerToken;
    protected Room testRoom;
    protected Category testCategory;
    protected Location testLocation;

    @PostConstruct
    void setupTestData() {
        Role userRole = roleRepository.findByName(RoleName.ROLE_USER)
                .orElseGet(() -> roleRepository.save(new Role(null, RoleName.ROLE_USER)));
        Role rentalerRole = roleRepository.findByName(RoleName.ROLE_RENTALER)
                .orElseGet(() -> roleRepository.save(new Role(null, RoleName.ROLE_RENTALER)));

        testUser = userRepository.findByEmail("testuser@example.com").orElseGet(() -> {
            User u = new User();
            u.setName("Test User");
            u.setEmail("testuser@example.com");
            u.setPhone("0912345678");
            u.setPassword(passwordEncoder.encode("password123"));
            u.setProvider(AuthProvider.local);
            u.setEmailVerified(true);
            u.setIsConfirmed(true);
            u.setRoles(new HashSet<>() {{ add(userRole); }});
            return userRepository.save(u);
        });

        testRentaler = userRepository.findByEmail("testrentaler@example.com").orElseGet(() -> {
            User u = new User();
            u.setName("Test Rentaler");
            u.setEmail("testrentaler@example.com");
            u.setPhone("0987654321");
            u.setPassword(passwordEncoder.encode("password123"));
            u.setProvider(AuthProvider.local);
            u.setEmailVerified(true);
            u.setIsConfirmed(true);
            u.setRoles(new HashSet<>() {{ add(rentalerRole); }});
            return userRepository.save(u);
        });

        testCategory = categoryRepository.findAll().stream().findFirst().orElseGet(() ->
                categoryRepository.save(new Category(null, "Phong tro", null))
        );

        testLocation = locationRepository.findAll().stream().findFirst().orElseGet(() ->
                locationRepository.save(new Location(null, "Ha Noi", null))
        );

        testRoom = roomRepository.findAll().stream().findFirst().orElseGet(() -> {
            Room r = new Room("Phong test", "Mo ta phong test",
                    BigDecimal.valueOf(2000000), 21.0285, 105.8542,
                    "123 Test Street", testRentaler.getName(), testRentaler.getName(),
                    testLocation, testCategory, testRentaler, RoomStatus.ROOM_RENT);
            r.setIsApprove(false);
            r.setIsRemove(false);
            return roomRepository.save(r);
        });
    }
}
