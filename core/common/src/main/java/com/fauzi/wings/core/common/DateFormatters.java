package com.fauzi.wings.core.common;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class DateFormatters {
    private static final SimpleDateFormat FULL =
            new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault());

    private DateFormatters() {}

    public static String full(long epochMs) {
        return FULL.format(new Date(epochMs));
    }
}
