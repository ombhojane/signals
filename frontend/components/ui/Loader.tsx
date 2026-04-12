"use client";

import Lottie from "lottie-react";
import rubiksAnimation from "@/public/Rubik's cube.json";

export function Loader({ fullScreen = false }: { fullScreen?: boolean }) {
  if (fullScreen) {
    return (
      <div
        className="fixed inset-0 flex items-center justify-center z-50"
        style={{
          backgroundColor: "rgba(14, 14, 14, 0.95)",
          backdropFilter: "blur(4px)",
        }}
      >
        <div className="flex flex-col items-center gap-6">
          <div className="w-48 h-48">
            <Lottie
              animationData={rubiksAnimation}
              loop={true}
              autoplay={true}
            />
          </div>
          <p
            className="text-sm font-medium tracking-wide"
            style={{ color: "#a7cbeb" }}
          >
            Loading...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center py-12">
      <div className="w-24 h-24">
        <Lottie
          animationData={rubiksAnimation}
          loop={true}
          autoplay={true}
        />
      </div>
    </div>
  );
}
