import React, { useRef, useState, useEffect } from "react";
import {
    View, StyleSheet, KeyboardAvoidingView, Platform, TextInput, TouchableOpacity,
    FlatList, Text, Alert, ScrollView, ActivityIndicator
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage"
import * as Speech from "expo-speech"
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { Ionicons } from "@expo/vector-icons";
import { useHeaderHeight } from "@react-navigation/elements";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "../utils/theme";
import AccessCodeModal from "./access_code";

const BASE_URL = "http://192.168.0.19:8000";

type Role = "user" | "ai";
type Message = { id: string; role: Role; text: string; };

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

    const [sessionEnded, setSessionEnded] = useState(false);
    const [finalizing, setFinalizing] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [downloadingPdf, setDownloadingPdf] = useState(false);  // ✅ NEW

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

    // Load chat history from backend
    const loadChatHistory = async (sessionId: number) => {
        console.log("📜 Loading chat history for session:", sessionId);
        setLoadingHistory(true);

        try {
            const response = await fetch(`${BASE_URL}/chat/${sessionId}/history`, {
                method: "GET",
            });

            if (!response.ok) {
                console.log("⚠️ Could not load chat history:", response.status);
                return;
            }

            const data = await response.json();
            console.log(`📜 Loaded ${data.message_count} previous messages`);

            if (data.messages && data.messages.length > 0) {
                const loadedMessages: Message[] = data.messages.map((msg: any) => ({
                    id: msg.id,
                    role: msg.role as Role,
                    text: msg.text
                }));

                setMessages([initialWelcomeMessage, ...loadedMessages]);

                setTimeout(() => {
                    const welcomeBack: Message = {
                        id: String(Date.now()),
                        role: "ai",
                        text: `📜 Welcome back! Loaded ${data.message_count} previous message(s). You can continue from where you left off.`
                    };
                    setMessages(prev => [...prev, welcomeBack]);
                }, 500);

                console.log("✅ Chat history loaded successfully");
            } else {
                console.log("ℹ️ No previous messages found - starting fresh");
            }

        } catch (error: any) {
            console.error("❌ Error loading chat history:", error.message);
        } finally {
            setLoadingHistory(false);
        }
    };

    const downloadPdfToPhone = async () => {
        if (!sessionId) {
            Alert.alert("Error", "No session found");
            return;
        }

        console.log("📥 Downloading PDF to phone...");
        setDownloadingPdf(true);

        try {
            const timestamp = new Date().getTime();
            const fileName = `symptom_report_${sessionId}_${timestamp}.pdf`;
            const fileUri = FileSystem.documentDirectory + fileName;

            console.log("📂 Saving to:", fileUri);

            const downloadResult = await FileSystem.downloadAsync(
                `${BASE_URL}/sessions/${sessionId}/download-pdf`,
                fileUri
            );

            console.log("✅ PDF downloaded:", downloadResult.uri);

            const canShare = await Sharing.isAvailableAsync();

            if (canShare) {
                await Sharing.shareAsync(downloadResult.uri, {
                    mimeType: 'application/pdf',
                    dialogTitle: 'Save Your Symptom Report',
                    UTI: 'com.adobe.pdf',
                });

                console.log("✅ PDF shared successfully");
            } else {
                Alert.alert(
                    "Download Complete",
                    `Your report has been downloaded as: ${fileName}`,
                    [{ text: "OK" }]
                );
            }

        } catch (error: any) {
            console.error("❌ Error downloading PDF:", error);
            Alert.alert(
                "Download Error",
                "Could not download your report. Please try again or ask your doctor for a copy.",
                [{ text: "OK" }]
            );
        } finally {
            setDownloadingPdf(false);
        }
    };

    const handleAccessGranted = (id: number) => {
        console.log("Access Granted with Session ID:", id);
        setSessionId(id);
        setAccessGranted(true);

        setTimeout(() => {
            loadChatHistory(id);
        }, 300);
    };

    const onSend = async () => {
        const trimmed = text.trim();

        if (!trimmed || sending || !sessionId || sessionEnded || loadingHistory) return;

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

    const confirmFinalize = () => {
        if (sessionEnded) {
            Alert.alert("Session Ended", "This session has already been finalized.");
            return;
        }

        if (collectedSymptoms.length === 0) {
            Alert.alert(
                "No Symptoms Recorded",
                "Please describe your symptoms before finalizing.",
                [{ text: "OK" }]
            );
            return;
        }

        Alert.alert(
            "Finish Session?",
            `This will generate a PDF report with ${collectedSymptoms.length} symptom(s) and end your session.\n\nContinue?`,
            [
                { text: "Cancel", style: "cancel" },
                { text: "Finalize", onPress: finalizeSession }
            ]
        );
    };

    const finalizeSession = async () => {
        if (!sessionId) {
            Alert.alert("Error", "No active session found");
            return;
        }

        setFinalizing(true);

        console.log("=== FINALIZING SESSION ===");
        console.log("Session ID:", sessionId);

        try {
            const response = await fetch(`${BASE_URL}/sessions/${sessionId}/finalize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });

            const data = await response.json();
            console.log("Finalize response:", data);

            if (response.ok) {
                setSessionEnded(true);

                const finalMsg: Message = {
                    id: String(Date.now()),
                    role: "ai",
                    text: "✅ Session completed! Your report has been generated and sent to your doctor. You can download a copy for yourself using the button below."
                };
                setMessages(prev => [...prev, finalMsg]);

                Alert.alert(
                    "✅ Session Complete!",
                    `Your symptom report has been generated.\n\n` +
                    `📄 ${collectedSymptoms.length} symptoms recorded\n` +
                    `📁 Report sent to your doctor\n` +
                    `📥 Use the "Download Report" button to save a copy\n\n` +
                    `Your session is now ended.`,
                    [{ text: "OK" }]
                );

                console.log("✅ Session finalized successfully");
            } else {
                Alert.alert("Error", data.detail || "Could not finalize session");
            }
        } catch (error: any) {
            console.error("Finalize error:", error);
            Alert.alert(
                "Connection Error",
                "Could not finalize session. Please check your connection."
            );
        } finally {
            setFinalizing(false);
        }
    };

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
                {/* Loading History Indicator */}
                {loadingHistory && (
                    <View style={styles.loadingBanner}>
                        <Ionicons name="time-outline" size={20} color="#007AFF" />
                        <Text style={styles.loadingText}>Loading previous messages...</Text>
                    </View>
                )}

                {/* Action Bar - Hide if session ended */}
                {sessionId && !sessionEnded && (
                    <View style={styles.topActionsContainer}>
                        <View style={{flex:1}}/>

                        {finalizing ? (
                            <View style={[styles.finishButton, {backgroundColor: '#999'}]}>
                                <Text style={styles.finishButtonText}>Finalizing...</Text>
                                <Ionicons name="hourglass-outline" size={16} color="white" />
                            </View>
                        ) : (
                            <TouchableOpacity
                                style={[
                                    styles.finishButton,
                                    collectedSymptoms.length === 0 && {opacity: 0.5}
                                ]}
                                onPress={confirmFinalize}
                                disabled={collectedSymptoms.length === 0}
                            >
                                <Text style={styles.finishButtonText}>
                                    Finish & Send ({collectedSymptoms.length})
                                </Text>
                                <Ionicons name="document-text-outline" size={16} color="white" />
                            </TouchableOpacity>
                        )}
                    </View>
                )}

                {/* ✅ Session Ended Banner + Download Section */}
                {sessionEnded && (
                    <>
                        <View style={styles.sessionEndedBanner}>
                            <Ionicons name="checkmark-circle" size={24} color="#34C759" />
                            <Text style={styles.sessionEndedText}>Session Ended - Report Sent</Text>
                        </View>

                        {/* ✅ Download Button Section */}
                        <View style={styles.downloadContainer}>
                            <Text style={styles.downloadTitle}>Your Report</Text>
                            <Text style={styles.downloadSubtitle}>
                                Your symptom report has been sent to your doctor.
                                Download a copy to save on your phone.
                            </Text>

                            <TouchableOpacity
                                style={[
                                    styles.downloadButton,
                                    downloadingPdf && styles.downloadButtonDisabled
                                ]}
                                onPress={downloadPdfToPhone}
                                disabled={downloadingPdf}
                            >
                                {downloadingPdf ? (
                                    <>
                                        <ActivityIndicator size="small" color="white" />
                                        <Text style={styles.downloadButtonText}>Downloading...</Text>
                                    </>
                                ) : (
                                    <>
                                        <Ionicons name="download-outline" size={22} color="white" />
                                        <Text style={styles.downloadButtonText}>Download My Report</Text>
                                    </>
                                )}
                            </TouchableOpacity>

                            <Text style={styles.downloadHint}>
                                💡 Tip: You can save it to Files, iCloud, or share via AirDrop
                            </Text>
                        </View>
                    </>
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

                {/* Bottom Bar - Hide if session ended */}
                {!sessionEnded && (
                    <View style={[styles.bottomBar, { backgroundColor: colors.card, paddingBottom: Math.max(10, insets.bottom) }]}>
                        <View style={[styles.inputPill, { borderColor: colors.border, backgroundColor: 'white' }]}>
                            <TextInput
                                style={[styles.textInput, { color: 'black' }]}
                                placeholder={loadingHistory ? "Loading..." : "Type symptoms..."}
                                placeholderTextColor="gray"
                                value={text}
                                onChangeText={setText}
                                onSubmitEditing={onSend}
                                editable={!sessionEnded && !finalizing && !loadingHistory}
                            />
                            <TouchableOpacity
                                onPress={onSend}
                                disabled={sending || sessionEnded || finalizing || loadingHistory}
                            >
                                <Ionicons name="send" size={20} color={(sessionEnded || loadingHistory) ? "gray" : "dodgerblue"} />
                            </TouchableOpacity>
                        </View>
                    </View>
                )}

                {/* Session Ended Footer */}
                {sessionEnded && (
                    <View style={styles.sessionEndedFooter}>
                        <Ionicons name="lock-closed" size={18} color="#666" />
                        <Text style={styles.sessionEndedFooterText}>
                            This session has ended. Your report is with your doctor.
                        </Text>
                    </View>
                )}
            </KeyboardAvoidingView>

            <AccessCodeModal
                visible={!accessGranted}
                onAccessGranted={handleAccessGranted}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    loadingBanner: {
        flexDirection: 'row',
        backgroundColor: '#e3f2fd',
        paddingVertical: 10,
        paddingHorizontal: 16,
        alignItems: 'center',
        justifyContent: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#bbdefb',
    },
    loadingText: {
        marginLeft: 8,
        fontSize: 14,
        color: '#1976d2',
        fontWeight: '500',
    },

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
        backgroundColor: '#34C759',
        paddingVertical: 30,
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

    sessionEndedBanner: {
        flexDirection: 'row',
        backgroundColor: '#e8f5e9',
        paddingVertical: 12,
        paddingHorizontal: 16,
        alignItems: 'center',
        justifyContent: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#c8e6c9',
    },
    sessionEndedText: {
        marginLeft: 10,
        fontSize: 16,
        fontWeight: '600',
        color: '#2e7d32',
    },

    // ✅ NEW: Download section styles
    downloadContainer: {
        backgroundColor: '#ffffff',
        paddingHorizontal: 20,
        paddingVertical: 16,
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 3,
        elevation: 2,
    },
    downloadTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#333',
        marginBottom: 6,
    },
    downloadSubtitle: {
        fontSize: 14,
        color: '#666',
        marginBottom: 16,
        lineHeight: 20,
    },
    downloadButton: {
        flexDirection: 'row',
        backgroundColor: '#007AFF',
        paddingVertical: 14,
        paddingHorizontal: 20,
        borderRadius: 12,
        alignItems: 'center',
        justifyContent: 'center',
        shadowColor: "#007AFF",
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 6,
        elevation: 4,
    },
    downloadButtonDisabled: {
        backgroundColor: '#999',
        shadowOpacity: 0.1,
    },
    downloadButtonText: {
        color: 'white',
        fontSize: 16,
        fontWeight: '600',
        marginLeft: 10,
    },
    downloadHint: {
        fontSize: 12,
        color: '#888',
        marginTop: 12,
        textAlign: 'center',
        fontStyle: 'italic',
    },

    sessionEndedFooter: {
        flexDirection: 'row',
        backgroundColor: '#f5f5f5',
        paddingVertical: 16,
        paddingHorizontal: 20,
        alignItems: 'center',
        justifyContent: 'center',
        borderTopWidth: 1,
        borderTopColor: '#e0e0e0',
    },
    sessionEndedFooterText: {
        marginLeft: 10,
        fontSize: 14,
        color: '#666',
        textAlign: 'center',
    },

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