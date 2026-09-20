package com.cntt.rentalmanagement.services;

import com.cntt.rentalmanagement.domain.enums.AuthProvider;
import com.cntt.rentalmanagement.domain.enums.RoleName;
import com.cntt.rentalmanagement.domain.models.Role;
import com.cntt.rentalmanagement.domain.models.User;
import com.cntt.rentalmanagement.domain.payload.request.EmailRequest;
import com.cntt.rentalmanagement.domain.payload.request.LoginRequest;
import com.cntt.rentalmanagement.domain.payload.request.SignUpRequest;
import com.cntt.rentalmanagement.exception.BadRequestException;
import com.cntt.rentalmanagement.repository.RoleRepository;
import com.cntt.rentalmanagement.repository.UserRepository;
import com.cntt.rentalmanagement.secruity.TokenProvider;
import com.cntt.rentalmanagement.services.impl.AuthServiceImpl;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private RoleRepository roleRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private AuthenticationManager authenticationManager;

    @Mock
    private TokenProvider tokenProvider;

    @InjectMocks
    private AuthServiceImpl authService;

    @Test
    @DisplayName("Login - Thanh cong")
    void loginSuccess() {
        LoginRequest request = new LoginRequest();
        request.setEmail("test@gmail.com");
        request.setPassword("password");

        Authentication auth = mock(Authentication.class);
        when(authenticationManager.authenticate(any())).thenReturn(auth);
        when(tokenProvider.createToken(auth)).thenReturn("mock-jwt-token");

        String token = authService.login(request);
        assertThat(token).isEqualTo("mock-jwt-token");
        verify(authenticationManager).authenticate(any());
        verify(tokenProvider).createToken(auth);
    }

    @Test
    @DisplayName("Register - Thanh cong voi role USER")
    void registerSuccessAsUser() throws Exception {
        SignUpRequest request = new SignUpRequest();
        request.setName("New User");
        request.setEmail("newuser@gmail.com");
        request.setPassword("password123");
        request.setConfirmPassword("password123");
        request.setPhone("0912345678");
        request.setRole(RoleName.ROLE_USER);

        Role userRole = new Role(RoleName.ROLE_USER);

        when(userRepository.existsByEmail("newuser@gmail.com")).thenReturn(false);
        when(userRepository.findByPhone("0912345678")).thenReturn(Optional.empty());
        when(roleRepository.findByName(RoleName.ROLE_USER)).thenReturn(Optional.of(userRole));
        when(passwordEncoder.encode("password123")).thenReturn("encodedPassword");

        var result = authService.registerAccount(request);
        assertThat(result).isNotNull();
        verify(userRepository).save(any(User.class));
    }

    @Test
    @DisplayName("Register - Thanh cong voi role RENTALER")
    void registerSuccessAsRentaler() throws Exception {
        SignUpRequest request = new SignUpRequest();
        request.setName("New Rentaler");
        request.setEmail("newrentaler@gmail.com");
        request.setPassword("password123");
        request.setConfirmPassword("password123");
        request.setPhone("0987654321");
        request.setAddress("123 Test Street");
        request.setRole(RoleName.ROLE_RENTALER);

        Role rentalerRole = new Role(RoleName.ROLE_RENTALER);

        when(userRepository.existsByEmail("newrentaler@gmail.com")).thenReturn(false);
        when(userRepository.findByPhone("0987654321")).thenReturn(Optional.empty());
        when(roleRepository.findByName(RoleName.ROLE_RENTALER)).thenReturn(Optional.of(rentalerRole));
        when(passwordEncoder.encode("password123")).thenReturn("encodedPassword");

        var result = authService.registerAccount(request);
        assertThat(result).isNotNull();
        verify(userRepository).save(any(User.class));
    }

    @Test
    @DisplayName("Register - Email da ton tai")
    void registerDuplicateEmail() {
        SignUpRequest request = new SignUpRequest();
        request.setName("Existing User");
        request.setEmail("existing@gmail.com");
        request.setPassword("password123");
        request.setConfirmPassword("password123");
        request.setPhone("0911111111");
        request.setRole(RoleName.ROLE_USER);

        when(userRepository.existsByEmail("existing@gmail.com")).thenReturn(true);

        assertThatThrownBy(() -> authService.registerAccount(request))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    @DisplayName("Register - Mat khau khong khop")
    void registerPasswordMismatch() {
        SignUpRequest request = new SignUpRequest();
        request.setName("User");
        request.setEmail("user@gmail.com");
        request.setPassword("password123");
        request.setConfirmPassword("differentpassword");
        request.setPhone("0912345678");
        request.setRole(RoleName.ROLE_USER);

        when(userRepository.existsByEmail("user@gmail.com")).thenReturn(false);
        when(userRepository.findByPhone("0912345678")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.registerAccount(request))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("không khớp");
    }

    @Test
    @DisplayName("Register - Email khong phai @gmail.com")
    void registerInvalidEmailDomain() {
        SignUpRequest request = new SignUpRequest();
        request.setName("User");
        request.setEmail("user@yahoo.com");
        request.setPassword("password123");
        request.setConfirmPassword("password123");
        request.setPhone("0912345678");
        request.setRole(RoleName.ROLE_USER);

        when(userRepository.existsByEmail("user@yahoo.com")).thenReturn(false);
        when(userRepository.findByPhone("0912345678")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.registerAccount(request))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("email");
    }

    @Test
    @DisplayName("Forgot password - Thanh cong")
    void forgotPasswordSuccess() throws Exception {
        EmailRequest request = new EmailRequest();
        request.setEmail("test@gmail.com");

        User user = new User();
        user.setEmail("test@gmail.com");

        when(userRepository.findByEmail("test@gmail.com")).thenReturn(Optional.of(user));

        var result = authService.forgotPassword(request);
        assertThat(result).isNotNull();
        assertThat(result.getMessage()).contains("thành công");
    }

    @Test
    @DisplayName("Forgot password - Email khong ton tai")
    void forgotPasswordEmailNotFound() {
        EmailRequest request = new EmailRequest();
        request.setEmail("nonexistent@gmail.com");

        when(userRepository.findByEmail("nonexistent@gmail.com")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.forgotPassword(request))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    @DisplayName("Lock account - Khoa tai khoan")
    void lockAccountSuccess() {
        User user = new User();
        user.setId(1L);
        user.setIsLocked(false);

        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        var result = authService.lockAccount(1L);
        assertThat(result).isNotNull();
        assertThat(result.getMessage()).contains("thành công");
        verify(userRepository).save(any(User.class));
    }

    @Test
    @DisplayName("Lock account - Mo khoa tai khoan")
    void unlockAccountSuccess() {
        User user = new User();
        user.setId(2L);
        user.setIsLocked(true);

        when(userRepository.findById(2L)).thenReturn(Optional.of(user));

        var result = authService.lockAccount(2L);
        assertThat(result).isNotNull();
        verify(userRepository).save(argThat(u -> !((User) u).getIsLocked()));
    }

    @Test
    @DisplayName("Confirm account - Xac thuc tai khoan")
    void confirmAccountSuccess() {
        EmailRequest request = new EmailRequest();
        request.setEmail("test@gmail.com");

        User user = new User();
        user.setEmail("test@gmail.com");
        user.setIsConfirmed(false);

        when(userRepository.findByEmail("test@gmail.com")).thenReturn(Optional.of(user));

        var result = authService.confirmedAccount(request);
        assertThat(result).isNotNull();
        assertThat(result.getMessage()).contains("xác thực");
        verify(userRepository).save(argThat(u -> ((User) u).getIsConfirmed()));
    }
}
