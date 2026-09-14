import React from "react";
import Header from "../../common/Header";
import IntroCarosel from "../../common/IntroCarousel";
import Home from "../../common/Home";
import Footer from "../../common/Footer";

function Main(props) {
  return (
    <>
      <Header authenticated={props.authenticated} currentUser={props.currentUser} onLogout={props.onLogout}/>
      <IntroCarosel />
      <Home />
      <Footer />
    </>
  );
}

export default Main;