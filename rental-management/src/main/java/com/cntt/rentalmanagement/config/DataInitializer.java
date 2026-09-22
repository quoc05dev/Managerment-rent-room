package com.cntt.rentalmanagement.config;

import com.cntt.rentalmanagement.domain.enums.AuthProvider;
import com.cntt.rentalmanagement.domain.enums.RoleName;
import com.cntt.rentalmanagement.domain.models.Role;
import com.cntt.rentalmanagement.domain.models.User;
import com.cntt.rentalmanagement.repository.RoleRepository;
import com.cntt.rentalmanagement.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.util.Collections;

@Component
@RequiredArgsConstructor
@Slf4j
@Profile("!test")
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {
        promoteToAdmin("dangminhquoc8@gmail.com");
    }

    private void promoteToAdmin(String email) {
        User user = userRepository.findByEmail(email).orElse(null);
        if (user == null) {
            log.info("=== User {} not found, skipping admin promotion ===", email);
            return;
        }
        boolean alreadyAdmin = user.getRoles().stream()
                .anyMatch(r -> r.getName() == RoleName.ROLE_ADMIN);
        if (alreadyAdmin) {
            log.info("=== User {} is already ADMIN ===", email);
            return;
        }
        Role adminRole = roleRepository.findByName(RoleName.ROLE_ADMIN)
                .orElseThrow(() -> new IllegalArgumentException("ROLE_ADMIN not found"));
        user.setRoles(Collections.singleton(adminRole));
        userRepository.save(user);
        log.info("=== User {} promoted to ADMIN ===", email);
    }
}
