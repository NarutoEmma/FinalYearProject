// Import the Stack navigator from expo-router. This lets us define a stack of screens
// and automatically connect files in the /app folder as screens based on their filenames.
import { Stack } from "expo-router";
import React from "react";
import { ThemeProvider, useTheme } from "../utils/theme";

//themed stack navigator with app colors
function ThemedStack() {
    const { colors } = useTheme();
    return (
        <ThemeProvider>
            <Stack>
                <Stack.Screen name="index" options={{headerShown: false, gestureEnabled:false}}/>

            </Stack>
        </ThemeProvider>
    );
}

//root layout providing theme context
export default function RootLayout() {
    // Returning <Stack /> tells expo-router to use a native-like stack navigation.
    // Each file in the /app directory (like home.tsx, notification.tsx) becomes a screen.
    return (
        <ThemeProvider>
            <ThemedStack />
        </ThemeProvider>
    );
}
