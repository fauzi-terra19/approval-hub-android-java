package com.fauzi.wings.domain.approval;

import com.fauzi.wings.core.model.RequestType;

public final class AmountBasedRules {
    public static final double PURCHASE_L3_THRESHOLD = 10_000_000.0;
    public static final double PURCHASE_L2_THRESHOLD = 2_000_000.0;
    public static final double EXPENSE_L3_THRESHOLD = 5_000_000.0;

    private AmountBasedRules() {}

    public static int requiredMaxLevel(RequestType type, double amount) {
        switch (type) {
            case PURCHASE:
                if (amount > PURCHASE_L3_THRESHOLD) return 3;
                if (amount > PURCHASE_L2_THRESHOLD) return 2;
                return 1;
            case EXPENSE:
                return amount > EXPENSE_L3_THRESHOLD ? 3 : 2;
            case LEAVE:
            case ACCESS:
            default:
                return 2;
        }
    }

    public static String ruleLabel(RequestType type, double amount) {
        int max = requiredMaxLevel(type, amount);
        return "Wajib sampai L" + max + " (rule " + type.name() + ")";
    }
}
