package com.fauzi.wings.core.model;

public class User {
    public final long id;
    public final String username;
    public final String displayName;
    public final Role role;
    public final String department;

    public User(long id, String username, String displayName, Role role, String department) {
        this.id = id;
        this.username = username;
        this.displayName = displayName;
        this.role = role;
        this.department = department;
    }
}
