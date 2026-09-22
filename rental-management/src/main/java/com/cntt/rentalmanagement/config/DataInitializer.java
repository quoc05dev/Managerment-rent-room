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
        createAdminIfNotExists("admin@gmail.com", "Admin", "admin123", "0900000000");
        createRentalerIfNotExists("rentaler@gmail.com", "Test Rentaler", "rentaler123", "0911111111");
    }

    private void createAdminIfNotExists(String email, String name, String password, String phone) {
        if (userRepository.existsByEmail(email)) return;
        Role adminRole = roleRepository.findByName(RoleName.ROLE_ADMIN)
                .orElseThrow(() -> new IllegalArgumentException("ROLE_ADMIN not found"));
        User admin = new User();
        admin.setEmail(email);
        admin.setName(name);
        admin.setPassword(passwordEncoder.encode(password));
        admin.setProvider(AuthProvider.local);
        admin.setIsConfirmed(true);
        admin.setIsLocked(false);
        admin.setPhone(phone);
        admin.setRoles(Collections.singleton(adminRole));
        userRepository.save(admin);
        log.info("=== Admin account created: {} / {} ===", email, password);
    }

    private void createRentalerIfNotExists(String email, String name, String password, String phone) {
        if (userRepository.existsByEmail(email)) return;
        Role rentalerRole = roleRepository.findByName(RoleName.ROLE_RENTALER)
                .orElseThrow(() -> new IllegalArgumentException("ROLE_RENTALER not found"));
        User rentaler = new User();
        rentaler.setEmail(email);
        rentaler.setName(name);
        rentaler.setPassword(passwordEncoder.encode(password));
        rentaler.setProvider(AuthProvider.local);
        rentaler.setIsConfirmed(true);
        rentaler.setIsLocked(false);
        rentaler.setPhone(phone);
        rentaler.setRoles(Collections.singleton(rentalerRole));
        userRepository.save(rentaler);
        log.info("=== Rentaler account created: {} / {} ===", email, password);
    }
}
