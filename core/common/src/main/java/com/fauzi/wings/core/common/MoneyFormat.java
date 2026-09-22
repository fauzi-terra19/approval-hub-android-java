package com.fauzi.wings.core.common;

import java.text.NumberFormat;
import java.util.Locale;

public final class MoneyFormat {
    private static final NumberFormat IDR = NumberFormat.getCurrencyInstance(new Locale("in", "ID"));
    private MoneyFormat() {}
    public static String format(double amount) {
        if (amount <= 0.0) return "-";
        return IDR.format(amount);
    }
}
