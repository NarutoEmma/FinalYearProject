import React, { useRef, useState, useEffect } from "react";
import {
    View, StyleSheet, KeyboardAvoidingView, Platform, TextInput, TouchableOpacity, FlatList, Text, Alert
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage"
import * as Speech from "expo-speech"
import { Ionicons } from "@expo/vector-icons";
import { useHeaderHeight } from "@react-navigation/elements";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "../utils/theme";
// Make sure this path is correct! If access_code.tsx is in 'components', use "../components/access_code"
import AccessCodeModal from "./access_code";

// ⚠️ IMPORTANT: Use your computer's local IP (e.g., 192.168.1.5) instead of 127.0.0.1 for physical devices/emulators
const BASE_URL = "http://192.168.0.19:8000"; // Use 10.0.2.2 for Android Emulator, or your LAN IP for physical device

type Role = "user" | "ai";
type Message = { id: string; role: Role; text: string; };

const initialWelcomeMessage: Message = {
    id: "m1",
    role: "ai",
    text: "Hello. I am your triage assistant. What is your main symptom today?"
};

export default function BeginFocus() {
    const [sessionId, setSessionId] = useState<number | null>(null);
    const [accessGranted, setAccessGranted] = useState(false);

    const [text, setText] = useState("");
    const [messages, setMessages] = useState<Message[]>([initialWelcomeMessage]);
    const [sending, setSending] = useState(false);
    const [speaking, setSpeaking] = useState<boolean>(false);

    const listRef = useRef<FlatList<Message>>(null);
    const { colors } = useTheme();
    const insets = useSafeAreaInsets();

    // Safety check for header height
    const headerHeight = useHeaderHeight() || 0;
    const keyboardOffset = Platform.select({ ios: headerHeight, android: 0 }) as number;

    // Auto-scroll logic
    useEffect(() => {
        setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }, [messages]);

    // 1. FIX: Define the handler
    const handleAccessGranted = (id: number) => {
        console.log("Access Granted with Session ID:", id);
        setSessionId(id);
        setAccessGranted(true);
    };

    const onSend = async () => {
        const trimmed = text.trim();
        if (!trimmed || sending || !sessionId) return;

        const userMsg: Message = { id: String(Date.now()), role: "user", text: trimmed };
        setMessages((prev) => [...prev, userMsg]);
        setText("");
        setSending(true);

        try {
            const response = await fetch(`${BASE_URL}/chat/${sessionId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content: trimmed }), // Ensure backend expects 'content'
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            const aiText = data.reply || "I'm having trouble thinking.";

            const aiMsg: Message = { id: String(Date.now() + 1), role: "ai", text: aiText };
            setMessages(prev => [...prev, aiMsg]);
        } catch (err: any) {
            const errorMsg: Message = { id: String(Date.now() + 1), role: "ai", text: "Connection Error. Check your IP/Server." };
            setMessages(prev => [...prev, errorMsg]);
            console.error(err);
        } finally {
            setSending(false);
        }
    };

    const readText = (text: string) => {
        if (speaking) { Speech.stop(); setSpeaking(false); return; }
        setSpeaking(true);
        Speech.speak(text, { onDone: () => setSpeaking(false), onStopped: () => setSpeaking(false) });
    };

    const renderItem = ({ item }: { item: Message }) => {
        const isUser = item.role === "user";
        return (
            <View style={[styles.row, isUser ? styles.rowRight : styles.rowLeft]}>
                <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
                    <Text style={[styles.messageText, isUser ? styles.userText : styles.aiText]}>{item.text}</Text>
                </View>
                {!isUser && (
                    <TouchableOpacity style={styles.ttsButton} onPress={() => readText(item.text)}>
                        <Ionicons name={speaking ? "stop-circle-outline" : "mic-outline"} size={18} color={colors.text as string} />
                    </TouchableOpacity>
                )}
            </View>
        );
    };

    return (
        <View style={{ flex: 1, backgroundColor: colors.background }}>
            <KeyboardAvoidingView
                style={{ flex: 1 }}
                behavior={Platform.OS === "ios" ? "padding" : "height"}
                keyboardVerticalOffset={keyboardOffset}
            >
                <FlatList
                    ref={listRef}
                    data={messages}
                    renderItem={renderItem}
                    keyExtractor={item => item.id}
                    contentContainerStyle={{ paddingTop: 20, paddingHorizontal: 12, paddingBottom: 20 }}
                />

                <View style={[styles.bottomBar, { backgroundColor: colors.card, paddingBottom: Math.max(10, insets.bottom) }]}>
                    <View style={[styles.inputPill, { borderColor: colors.border, backgroundColor: 'white' }]}>
                        <TextInput
                            style={[styles.textInput, { color: 'black' }]}
                            placeholder="Type symptoms..."
                            placeholderTextColor="gray"
                            value={text}
                            onChangeText={setText}
                            onSubmitEditing={onSend}
                        />
                        <TouchableOpacity onPress={onSend} disabled={sending}>
                            <Ionicons name="send" size={20} color="dodgerblue" />
                        </TouchableOpacity>
                    </View>
                </View>
            </KeyboardAvoidingView>

            {/* 2. FIX: Pass the handler correctly */}
            <AccessCodeModal
                visible={!accessGranted}
                onAccessGranted={handleAccessGranted}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    row: { width: "100%", marginBottom: 8, flexDirection: "row", alignItems: 'flex-end' },
    rowLeft: { justifyContent: "flex-start" },
    rowRight: { justifyContent: "flex-end" },
    bubble: { maxWidth: "80%", padding: 12, borderRadius: 16 },
    aiBubble: { backgroundColor: "#E5E5EA", borderBottomLeftRadius: 4 },
    userBubble: { backgroundColor: "#007AFF", borderBottomRightRadius: 4 },
    messageText: { fontSize: 16 },
    aiText: { color: "black" },
    userText: { color: "white" },
    bottomBar: { padding: 10, borderTopWidth: 1, borderTopColor: "#eee" },
    inputPill: { flexDirection: "row", alignItems: "center", borderWidth: 1, borderRadius: 25, paddingHorizontal: 15, paddingVertical: 5 },
    textInput: { flex: 1, height: 40, marginRight: 10 },
    ttsButton: { marginLeft: 5, padding: 5 },
});