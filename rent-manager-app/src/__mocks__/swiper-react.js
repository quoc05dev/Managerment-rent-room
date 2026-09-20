import React from 'react';

const Swiper = ({ children, ...props }) => <div data-testid="swiper">{children}</div>;
const SwiperSlide = ({ children, ...props }) => <div data-testid="swiper-slide">{children}</div>;

export { Swiper, SwiperSlide };
