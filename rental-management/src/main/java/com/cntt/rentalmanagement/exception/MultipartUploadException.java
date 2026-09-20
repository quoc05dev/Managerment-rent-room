package com.cntt.rentalmanagement.exception;

import com.cntt.rentalmanagement.domain.payload.response.MessageResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@RestControllerAdvice
public class MultipartUploadException {

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public String handlerFileUpload(MaxUploadSizeExceededException exception, HttpServletRequest httpServletRequest, HttpServletResponse httpServletResponse){
        return "Dung lượng của file quá 1MB. Mong người dùng kiểm tra lại";
    }

    @ExceptionHandler({ IllegalArgumentException.class })
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public ResponseEntity<?> handleException(IllegalArgumentException e) {
        return ResponseEntity.ok(MessageResponse.builder().message("Đăng nhập để sử dụng chức năng.").build());
    }

    @ExceptionHandler({ BadRequestException.class })
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public ResponseEntity<?> handleBadRequestException(BadRequestException e) {
        return ResponseEntity.ok(MessageResponse.builder().message(e.getMessage()).build());
    }

    @ExceptionHandler({ Exception.class })
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ResponseEntity<?> handleException(Exception e) {
        return ResponseEntity.ok(MessageResponse.builder().message("Đã có lỗi xảy ra. Vui lòng thử lại.").build());
    }
}
