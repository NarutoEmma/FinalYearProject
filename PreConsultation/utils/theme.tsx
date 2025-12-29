import React, { createContext, useContext, useMemo, useState } from "react";
import { ColorValue } from "react-native";

type Palette = {
    background: ColorValue;
    card: ColorValue;
    text: ColorValue;
    subtleText: ColorValue;
    border: ColorValue;
    primary: ColorValue;
};

const LightColors: Palette = {
    background: "whitesmoke",
    card: "white",
    text: "black",
    subtleText: "dimgray",
    border: "gainsboro",
    primary: "dodgerblue",
};

const DarkColors: Palette = {
    background: "black",
    card: "dimgray",
    text: "white",
    subtleText: "silver",
    border: "darkgray",
    primary: "dodgerblue",
};

type ThemeContextValue = {
    isDark: boolean;
    colors: Palette;
    toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

//theme provider managing light/dark palette
export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [isDark, setIsDark] = useState(false);

    const value = useMemo<ThemeContextValue>(() => ({
        isDark,
        colors: isDark ? DarkColors : LightColors,
        toggleTheme: () => setIsDark((v) => !v),
    }), [isDark]);

    return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

//hook to access theme context
export function useTheme() {
    const ctx = useContext(ThemeContext);
    if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
    return ctx;
}
