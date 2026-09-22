package com.fauzi.wings.core.common;

import java.text.NumberFormat;
import java.util.Locale;

public final class MoneyFormatters {
    private MoneyFormatters() {}

    public static String idr(double amount) {
        NumberFormat nf = NumberFormat.getCurrencyInstance(new Locale("id", "ID"));
        return nf.format(amount);
    }
}
