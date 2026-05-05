"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, systemTheme } = useTheme();

  // useEffect only runs on the client, so now we can safely show the UI
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button className="relative flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground transition-all opacity-0">
        <span className="material-symbols-outlined text-[1.3rem]">light_mode</span>
      </button>
    );
  }

  // Determine the actual current theme (system theme if set to system)
  const currentTheme = theme === "system" ? systemTheme : theme;
  const isDark = currentTheme === "dark";

  // Cycle through: system -> light -> dark -> system
  const handleCycleTheme = () => {
    if (theme === "system") {
      setTheme("light");
    } else if (theme === "light") {
      setTheme("dark");
    } else {
      setTheme("system");
    }
  };

  const getThemeLabel = () => {
    if (theme === "system") return "system (auto)";
    return theme || "light";
  };

  return (
    <button
      onClick={handleCycleTheme}
      className="relative flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/10 transition-all active:scale-95 group cursor-pointer"
      title={`Theme: ${getThemeLabel()} (click to cycle)`}
    >
      <span className="material-symbols-outlined text-[1.3rem] group-hover:scale-110 transition-transform">
        {isDark ? "light_mode" : "dark_mode"}
      </span>
    </button>
  );
}
