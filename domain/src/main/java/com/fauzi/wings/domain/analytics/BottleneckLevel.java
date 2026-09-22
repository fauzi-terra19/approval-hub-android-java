package com.fauzi.wings.domain.analytics;

public class BottleneckLevel {
    public final int level;
    public final double avgWaitHours;
    public final int sampleCount;

    public BottleneckLevel(int level, double avgWaitHours, int sampleCount) {
        this.level = level;
        this.avgWaitHours = avgWaitHours;
        this.sampleCount = sampleCount;
    }
}
