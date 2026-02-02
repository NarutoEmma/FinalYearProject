import React, { useRef, useState, useEffect } from "react";
import {
    View, StyleSheet, KeyboardAvoidingView, Platform, TextInput, TouchableOpacity, FlatList, Text, Alert, ScrollView
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage"
import * as Speech from "expo-speech"
import { Ionicons } from "@expo/vector-icons";
import { useHeaderHeight } from "@react-navigation/elements";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "../utils/theme";
// Make sure this path is correct!
import AccessCodeModal from "./access_code";

// ⚠️ IMPORTANT: Use your computer's local IP (Check ipconfig)
const BASE_URL = "http://192.168.0.24:8000";

type Role = "user" | "ai";
type Message = { id: string; role: Role; text: string; };

// Type for the symptom data
type Symptom = {
    symptom: string;
    severity?: string;
    duration?: string;
    frequency?: string;
};

const initialWelcomeMessage: Message = {
    id: "m1",
    role: "ai",
    text: "Hello. I am your triage assistant. What is your main symptom today?"
};

export default function BeginFocus() {
    const [sessionId, setSessionId] = useState<number | null>(null);
    const [accessGranted, setAccessGranted] = useState(false);

    // State for collected symptoms
    const [collectedSymptoms, setCollectedSymptoms] = useState<Symptom[]>([]);

    const [text, setText] = useState("");
    const [messages, setMessages] = useState<Message[]>([initialWelcomeMessage]);
    const [sending, setSending] = useState(false);
    const [speaking, setSpeaking] = useState<boolean>(false);

    const listRef = useRef<FlatList<Message>>(null);
    const { colors } = useTheme();
    const insets = useSafeAreaInsets();

    const headerHeight = useHeaderHeight() || 0;
    const keyboardOffset = Platform.select({ ios: headerHeight, android: 0 }) as number;

    useEffect(() => {
        setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }, [messages]);

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
                body: JSON.stringify({ content: trimmed }),
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            const aiText = data.reply || "I'm having trouble thinking.";

            // Update the tracker with data from backend
            if (data.extracted && data.extracted.symptoms) {
                setCollectedSymptoms(data.extracted.symptoms);
            }

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

    // ✅ CONFIRMATION WRAPPER
    const confirmFinalize = () => {
        Alert.alert(
            "Finish Session",
            "Are you sure you want to finalize this session and send the report to your doctor?",
            [
                { text: "Cancel", style: "cancel" },
                { text: "Send Report", onPress: finalizeSession }
            ]
        );
    };

    const finalizeSession = async () =>{
        try {
            const response = await fetch(`${BASE_URL}/sessions/${sessionId}/finalize`, {
                method: "POST" });
            const data = await response.json();
            Alert.alert("Success", "Report sent to doctor!");
        }catch (error){
            console.error(error);
            Alert.alert("Error", "Could not send report to doctor.");
        }
    };

    // Render the symptom cards
    const renderSymptomTracker = () => {
        if (collectedSymptoms.length === 0) return null;

        return (
            <View style={[styles.trackerContainer, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[styles.trackerTitle, { color: colors.text }]}>Collected Information:</Text>
                <ScrollView style={{ maxHeight: 120 }} nestedScrollEnabled={true}>
                    {collectedSymptoms.map((s, index) => (
                        <View key={index} style={styles.symptomRow}>
                            <Text style={[styles.symptomName, { color: colors.text }]}>• {s.symptom || "Unknown"}</Text>
                            <View style={styles.tagsContainer}>
                                {s.severity ? <Text style={styles.tag}>{s.severity}</Text> : <Text style={styles.missingTag}>Needs Severity</Text>}
                                {s.duration ? <Text style={styles.tag}>{s.duration}</Text> : <Text style={styles.missingTag}>Needs Duration</Text>}
                                {s.frequency ? <Text style={styles.tag}>{s.frequency}</Text> : <Text style={styles.missingTag}>Needs Freq</Text>}
                            </View>
                        </View>
                    ))}
                </ScrollView>
            </View>
        );
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
                {/* ✅ NEW: Action Bar at the top */}
                {sessionId && (
                    <View style={styles.topActionsContainer}>
                        <View style={{flex:1}}/>
                        <TouchableOpacity style={styles.finishButton} onPress={confirmFinalize}>
                            <Text style={styles.finishButtonText}>Finish & Send</Text>
                            <Ionicons name="cloud-upload-outline" size={16} color="white" />
                        </TouchableOpacity>
                    </View>
                )}

                {/* Tracker Component */}
                {renderSymptomTracker()}

                <FlatList
                    ref={listRef}
                    data={messages}
                    renderItem={renderItem}
                    keyExtractor={item => item.id}
                    contentContainerStyle={{ paddingTop: 10, paddingHorizontal: 12, paddingBottom: 20 }}
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

            <AccessCodeModal
                visible={!accessGranted}
                onAccessGranted={handleAccessGranted}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    // ✅ NEW STYLES for top button
    topActionsContainer: {
        flexDirection: 'row',
        paddingHorizontal: 12,
        paddingTop: 10,
        paddingBottom: 5,
        justifyContent: 'flex-end',
        zIndex: 10
    },
    finishButton: {
        flexDirection: 'row',
        backgroundColor: '#34C759', // Nice medical green
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 20,
        alignItems: 'center',
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.2,
        shadowRadius: 1.41,
        elevation: 2,
    },
    finishButtonText: {
        color: 'white',
        fontWeight: '600',
        fontSize: 13,
        marginRight: 6
    },

    // Tracker styles
    trackerContainer: {
        marginHorizontal: 10,
        marginVertical: 5,
        padding: 10,
        borderRadius: 10,
        borderWidth: 1,
        elevation: 2,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
    },
    trackerTitle: {
        fontSize: 14,
        fontWeight: "bold",
        marginBottom: 5,
    },
    symptomRow: {
        marginBottom: 8,
        borderBottomWidth: 0.5,
        borderBottomColor: '#eee',
        paddingBottom: 4
    },
    symptomName: {
        fontSize: 16,
        fontWeight: "600",
        textTransform: 'capitalize'
    },
    tagsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        marginTop: 4,
    },
    tag: {
        backgroundColor: '#e1f5fe',
        color: '#0288d1',
        fontSize: 12,
        fontWeight: '600',
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4,
        marginRight: 5,
        overflow: 'hidden'
    },
    missingTag: {
        backgroundColor: '#ffebee',
        color: '#d32f2f',
        fontSize: 12,
        fontWeight: '600',
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4,
        marginRight: 5,
        overflow: 'hidden',
        borderWidth: 1,
        borderColor: '#ffcdd2'
    },
    // Existing styles...
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