package com.fauzi.wings.domain.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public final class PasswordHasher {
    private static final String PEPPER = "approvalhub_v2_pepper";

    private PasswordHasher() {}

    public static String hash(String rawPassword) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest((PEPPER + ":" + rawPassword).getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    public static boolean matches(String rawPassword, String storedHash) {
        return hash(rawPassword).equalsIgnoreCase(storedHash);
    }
}
