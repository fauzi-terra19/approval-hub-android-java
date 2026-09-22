package com.fauzi.wings.core.ui;

import android.net.Uri;
import android.os.Bundle;

public final class NavRoutes {
    public static final Uri LOGIN = Uri.parse("wings://login");
    public static final Uri DASHBOARD = Uri.parse("wings://dashboard");
    public static final Uri CREATE = Uri.parse("wings://create");

    private NavRoutes() {}

    public static Uri detail(long requestId) {
        return Uri.parse("wings://detail/" + requestId);
    }

    public static Bundle detailArgs(long requestId) {
        Bundle b = new Bundle();
        b.putLong("requestId", requestId);
        return b;
    }
}
