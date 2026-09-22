package com.fauzi.wings.core.model;

public class TypeStat {
    public final RequestType type;
    public final int count;
    public final double totalAmount;

    public TypeStat(RequestType type, int count, double totalAmount) {
        this.type = type;
        this.count = count;
        this.totalAmount = totalAmount;
    }
}
