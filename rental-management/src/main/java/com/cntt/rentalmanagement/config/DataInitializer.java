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
        ensureAdmin("dangminhquoc8@gmail.com", "Quoc DM", "admin123", "0900000000");
    }

    private void ensureAdmin(String email, String name, String password, String phone) {
        Role adminRole = roleRepository.findByName(RoleName.ROLE_ADMIN)
                .orElseThrow(() -> new IllegalArgumentException("ROLE_ADMIN not found"));

        User user = userRepository.findByEmail(email).orElse(null);
        if (user == null) {
            user = new User();
            user.setEmail(email);
            user.setName(name);
            user.setPassword(passwordEncoder.encode(password));
            user.setProvider(AuthProvider.local);
            user.setIsConfirmed(true);
            user.setIsLocked(false);
            user.setPhone(phone);
            user.setRoles(Collections.singleton(adminRole));
            userRepository.save(user);
            log.info("=== Admin account CREATED: {} ===", email);
        } else {
            boolean alreadyAdmin = user.getRoles().stream()
                    .anyMatch(r -> r.getName() == RoleName.ROLE_ADMIN);
            if (!alreadyAdmin) {
                user.getRoles().clear();
                user.setRoles(Collections.singleton(adminRole));
                userRepository.save(user);
                log.info("=== User {} PROMOTED to ADMIN ===", email);
            } else {
                log.info("=== User {} is already ADMIN ===", email);
            }
        }
    }
}
