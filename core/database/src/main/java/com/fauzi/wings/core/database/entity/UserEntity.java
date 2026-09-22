package com.fauzi.wings.core.database.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

import com.fauzi.wings.core.model.Role;

@Entity(tableName = "users")
public class UserEntity {
    @PrimaryKey
    public long id;
    public String username;
    public String displayName;
    public String passwordHash;
    public Role role;
    public String department;

    public UserEntity() {}

    public UserEntity(long id, String username, String displayName, String passwordHash, Role role, String department) {
        this.id = id;
        this.username = username;
        this.displayName = displayName;
        this.passwordHash = passwordHash;
        this.role = role;
        this.department = department;
    }
}
