package com.cntt.rentalmanagement.secruity;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

public class TokenAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private TokenProvider tokenProvider;

    @Autowired
    private CustomUserDetailsService customUserDetailsService;

    private static final Logger logger = LoggerFactory.getLogger(TokenAuthenticationFilter.class);

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        try {
            String jwt = getJwtFromRequest(request);
            if (StringUtils.hasText(jwt)) {
                logger.info("[JWT] Token found, length=" + jwt.length() + ", startsWith=" + jwt.substring(0, Math.min(20, jwt.length())));
                if (tokenProvider.validateToken(jwt)) {
                    logger.info("[JWT] Token VALIDATED OK");
                    Long userId = tokenProvider.getUserIdFromToken(jwt);
                    logger.info("[JWT] userId from token: " + userId);
                    UserDetails userDetails = customUserDetailsService.loadUserById(userId);
                    logger.info("[JWT] User loaded: " + userDetails.getUsername() + ", authorities: " + userDetails.getAuthorities());
                    UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
                    authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                    logger.info("[JWT] Authentication SET in context");
                } else {
                    logger.error("[JWT] Token VALIDATION FAILED for token length=" + jwt.length());
                }
            } else {
                logger.debug("[JWT] No token found in request " + request.getRequestURI());
            }
        } catch (Exception ex) {
            logger.error("[JWT] Could not set user authentication in security context for URI: " + request.getRequestURI(), ex);
        }

        filterChain.doFilter(request, response);
    }

    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7, bearerToken.length());
        }
        return null;
    }
}