package com.fauzi.wings.core.database.entity;

import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;
import androidx.room.PrimaryKey;

import com.fauzi.wings.core.model.ApprovalStatus;
import com.fauzi.wings.core.model.RequestType;

@Entity(
        tableName = "approval_requests",
        foreignKeys = @ForeignKey(
                entity = UserEntity.class,
                parentColumns = "id",
                childColumns = "requesterId",
                onDelete = ForeignKey.CASCADE
        ),
        indices = {@Index("requesterId"), @Index("status"), @Index("department")}
)
public class ApprovalRequestEntity {
    @PrimaryKey(autoGenerate = true)
    public long id;
    public String title;
    public String description;
    public RequestType type;
    public double amount;
    public long requesterId;
    public String department;
    public ApprovalStatus status;
    public int currentLevel;
    public int requiredMaxLevel;
    public boolean escalated;
    public long createdAt;
    public long updatedAt;

    public ApprovalRequestEntity() {}

    public ApprovalRequestEntity(String title, String description, RequestType type, double amount,
                                 long requesterId, String department, ApprovalStatus status,
                                 int currentLevel, int requiredMaxLevel, boolean escalated,
                                 long createdAt, long updatedAt) {
        this.title = title;
        this.description = description;
        this.type = type;
        this.amount = amount;
        this.requesterId = requesterId;
        this.department = department;
        this.status = status;
        this.currentLevel = currentLevel;
        this.requiredMaxLevel = requiredMaxLevel;
        this.escalated = escalated;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }
}
