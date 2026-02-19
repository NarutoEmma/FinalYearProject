import React, { useState } from "react";
import {
    View, StyleSheet, Text, TextInput, TouchableOpacity, Modal, Alert, ActivityIndicator
} from "react-native";
import { useTheme } from "../utils/theme";

interface AccessCodeModalProps {
    visible: boolean;
    onAccessGranted: (sessionId: number) => void;
}

// ✅ CORRECT IP and PORT
const API_URL = "http://192.168.0.19:8000";

export default function AccessCodeModal({ visible, onAccessGranted }: AccessCodeModalProps) {
    const [accessCode, setAccessCode] = useState("");
    const [loading, setLoading] = useState(false);
    const { colors } = useTheme();

    const validateCode = async () => {
        if (!accessCode.trim()) {
            Alert.alert("Error", "Please enter a code");
            return;
        }

        setLoading(true);

        try {
            // ✅ CORRECTED: Only one fetch, inside the try block
            // ✅ CORRECTED: Removed duplicate '/sessions' from URL
            const response = await fetch(`${API_URL}/sessions/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ access_code: accessCode }),
            });

            if (!response.ok) {
                // Try to parse error text safely
                const errorText = await response.text();
                let errorMessage = "Invalid Code";
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.detail) errorMessage = errorJson.detail;
                } catch (e) {
                    // If response wasn't JSON, use the raw text or status
                    if (errorText) errorMessage = errorText;
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            onAccessGranted(data.id);

        } catch (error: any) {
            console.error("Fetch error:", error);
            let msg = error.message;

            // Friendly error messages
            if (msg.includes("Network request failed")) {
                msg = "Could not connect to server. Check your computer IP and Firewall.";
            }

            Alert.alert("Verification Failed", msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal visible={visible} transparent={false} animationType="fade">
            <View style={[styles.modalOverlay, { backgroundColor: colors.background || 'white' }]}>
                <View style={styles.modalContent}>
                    <Text style={[styles.modalTitle, { color: 'black' }]}>Enter Verification Code</Text>
                    <TextInput
                        style={[styles.modalInput, { borderColor: '#ccc', color: 'black' }]}
                        placeholder="A1B2C3D4"
                        placeholderTextColor="#999"
                        value={accessCode}
                        onChangeText={setAccessCode}
                        autoCapitalize="characters"
                    />
                    <TouchableOpacity
                        style={[styles.modalButton, { backgroundColor: "dodgerblue" }]}
                        onPress={validateCode}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator color="white" />
                        ) : (
                            <Text style={styles.modalButtonText}>Start Session</Text>
                        )}
                    </TouchableOpacity>
                </View>
            </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    modalOverlay: { flex: 1, justifyContent: "center", alignItems: "center" },
    modalContent: { width: "85%", padding: 24, borderRadius: 16, backgroundColor: "white", elevation: 10 },
    modalTitle: { fontSize: 20, fontWeight: "bold", marginBottom: 20, textAlign: 'center' },
    modalInput: { width: "100%", height: 50, borderWidth: 1, borderRadius: 8, paddingHorizontal: 12, marginBottom: 20, fontSize: 18, textAlign: "center" },
    modalButton: { width: "100%", height: 50, borderRadius: 8, justifyContent: "center", alignItems: "center" },
    modalButtonText: { color: "white", fontSize: 18, fontWeight: "600" },
});