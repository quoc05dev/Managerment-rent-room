package com.cntt.rentalmanagement.secruity;


import com.cntt.rentalmanagement.domain.models.User;
import com.cntt.rentalmanagement.exception.ResourceNotFoundException;
import com.cntt.rentalmanagement.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;


import javax.transaction.Transactional;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    UserRepository userRepository;

    @Override
    @Transactional
    public UserDetails loadUserByUsername(String email)
            throws UsernameNotFoundException {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() ->
                        new UsernameNotFoundException("Email của bạn không tồn tại : " + email)
                );
        if (Boolean.TRUE.equals(user.getIsLocked()))
        {
            throw new LockedException("Tài khoản của bạn đã bị khóa. Lý do chi tiết sẽ có trong email của bạn.");
        }
        if (Boolean.FALSE.equals(user.getIsConfirmed())) {
            throw new DisabledException("Tài khoản của bạn chưa được xác thực. Vui lòng kiểm tra email để xác thực tài khoản.");
        }

        return UserPrincipal.create(user);
    }

    @Transactional
    public UserDetails loadUserById(Long id) {
        User user = userRepository.findById(id).orElseThrow(
                () -> new ResourceNotFoundException("User", "id", id)
        );

        return UserPrincipal.create(user);
    }
}