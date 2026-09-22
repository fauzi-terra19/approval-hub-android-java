package com.fauzi.wings.core.model;

public class MetricSnapshot {
    private final long id;
    private final String label;
    private final String category;
    private final double value;
    private final long recordedAt;

    public MetricSnapshot(long id, String label, String category, double value, long recordedAt) {
        this.id = id;
        this.label = label;
        this.category = category;
        this.value = value;
        this.recordedAt = recordedAt;
    }

    public long getId() { return id; }
    public String getLabel() { return label; }
    public String getCategory() { return category; }
    public double getValue() { return value; }
    public long getRecordedAt() { return recordedAt; }
}
