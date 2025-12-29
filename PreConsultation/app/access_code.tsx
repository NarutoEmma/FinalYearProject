import React, { useState } from "react";
import {
    View, StyleSheet, Text, TextInput, TouchableOpacity, Modal, Alert
} from "react-native";
import { useTheme } from "../utils/theme";

interface AccessCodeModalProps {
    visible: boolean;
    onAccessGranted: () => void;
}

export default function AccessCodeModal({ visible, onAccessGranted }: AccessCodeModalProps) {
    const [accessCode, setAccessCode] = useState("");
    const { colors } = useTheme();

    const validateCode = () => {
        // Simple validation for now, can be replaced with API call later
        if (accessCode === "1234") {
            onAccessGranted();
        } else {
            Alert.alert("Invalid Code", "Please enter a valid access code.");
        }
    };

    return (
        <Modal
            visible={visible}
            transparent={false}
            animationType="slide"
        >
            <View style={[styles.modalOverlay, { backgroundColor: colors.background }]}>
                <View style={styles.modalContent}>
                    <Text style={[styles.modalTitle, { color: colors.text }]}>Enter verification code</Text>
                    <TextInput
                        style={[styles.modalInput, { borderColor: colors.border, color: colors.text }]}
                        placeholder="Code"
                        placeholderTextColor={typeof colors.subtleText === 'string' ? colors.subtleText as string : undefined}
                        value={accessCode}
                        onChangeText={setAccessCode}
                        keyboardType="numeric"
                        secureTextEntry
                    />
                    <TouchableOpacity style={[styles.modalButton, { backgroundColor: "dodgerblue" }]} onPress={validateCode}>
                        <Text style={styles.modalButtonText}>Submit</Text>
                    </TouchableOpacity>
                </View>
            </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    modalOverlay: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
    },
    modalContent: {
        width: "80%",
        padding: 24,
        borderRadius: 16,
        backgroundColor: "white",
        elevation: 5,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        alignItems: "center",
    },
    modalTitle: {
        fontSize: 20,
        fontWeight: "bold",
        marginBottom: 20,
    },
    modalInput: {
        width: "100%",
        height: 50,
        borderWidth: 1,
        borderRadius: 8,
        paddingHorizontal: 12,
        marginBottom: 20,
        fontSize: 18,
        textAlign: "center",
    },
    modalButton: {
        width: "100%",
        height: 50,
        borderRadius: 8,
        justifyContent: "center",
        alignItems: "center",
    },
    modalButtonText: {
        color: "white",
        fontSize: 18,
        fontWeight: "600",
    },
});
