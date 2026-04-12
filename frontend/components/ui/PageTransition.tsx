"use client";

import { useEffect, useState, ReactNode } from "react";
import { Loader } from "./Loader";

interface PageTransitionProps {
  children: ReactNode;
  delay?: number;
}

export function PageTransition({ children, delay = 300 }: PageTransitionProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [showLoader, setShowLoader] = useState(true);

  useEffect(() => {
    // Show the page after the specified delay
    const loaderTimer = setTimeout(() => {
      setShowLoader(false);
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(loaderTimer);
  }, [delay]);

  return (
    <>
      {showLoader && <Loader fullScreen />}
      <div
        className="transition-opacity duration-500"
        style={{
          opacity: isVisible ? 1 : 0,
          pointerEvents: isVisible ? "auto" : "none",
        }}
      >
        {children}
      </div>
    </>
  );
}
