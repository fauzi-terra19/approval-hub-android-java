package com.fauzi.wings.core.model;

import java.util.Arrays;
import java.util.List;

public final class DemoAccounts {
    public static final class Demo {
        public final String username;
        public final String password;
        public final String roleLabel;

        public Demo(String username, String password, String roleLabel) {
            this.username = username;
            this.password = password;
            this.roleLabel = roleLabel;
        }
    }

    public static final List<Demo> ALL = Arrays.asList(
            new Demo("staff", "staff123", "STAFF"),
            new Demo("staff2", "staff123", "STAFF"),
            new Demo("supervisor", "spv123", "SUPERVISOR"),
            new Demo("manager", "mgr123", "MANAGER"),
            new Demo("director", "dir123", "DIRECTOR"),
            new Demo("admin", "admin123", "ADMIN")
    );

    private DemoAccounts() {}
}
