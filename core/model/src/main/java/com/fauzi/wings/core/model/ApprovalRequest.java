package com.fauzi.wings.core.model;

public class ApprovalRequest {
    public final long id;
    public final String title;
    public final String description;
    public final RequestType type;
    public final double amount;
    public final long requesterId;
    public final String department;
    public final ApprovalStatus status;
    public final int currentLevel;
    public final int requiredMaxLevel;
    public final boolean escalated;
    public final long createdAt;
    public final long updatedAt;

    public ApprovalRequest(long id, String title, String description, RequestType type, double amount,
                           long requesterId, String department, ApprovalStatus status, int currentLevel,
                           int requiredMaxLevel, boolean escalated, long createdAt, long updatedAt) {
        this.id = id;
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
