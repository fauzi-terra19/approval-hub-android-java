package com.fauzi.wings.core.model;

public class RequestFilter {
    public String query = "";
    public ApprovalStatus status;
    public RequestType type;
    public Double minAmount;
    public Double maxAmount;
    public String department;

    public boolean matches(ApprovalRequest request, String requesterName) {
        String q = query == null ? "" : query.trim();
        if (!q.isEmpty()) {
            String hay = (request.title + " " + request.description + " " + request.department + " " + requesterName).toLowerCase();
            if (!hay.contains(q.toLowerCase())) return false;
        }
        if (status != null && request.status != status) return false;
        if (type != null && request.type != type) return false;
        if (minAmount != null && request.amount < minAmount) return false;
        if (maxAmount != null && request.amount > maxAmount) return false;
        if (department != null && !department.isBlank() && !request.department.equalsIgnoreCase(department)) return false;
        return true;
    }
}
