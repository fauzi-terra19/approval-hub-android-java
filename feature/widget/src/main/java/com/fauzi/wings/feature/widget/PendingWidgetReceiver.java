package com.fauzi.wings.feature.widget;

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.widget.RemoteViews;

import com.fauzi.wings.core.database.AppDatabase;

public class PendingWidgetReceiver extends AppWidgetProvider {
    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        AppDatabase.IO.execute(() -> {
            int count = 0;
            try {
                count = AppDatabase.get(context).approvalRequestDao().pendingCountSync();
            } catch (Exception ignored) {
            }
            int finalCount = count;
            new Handler(Looper.getMainLooper()).post(() -> {
                for (int id : appWidgetIds) {
                    RemoteViews views = new RemoteViews(context.getPackageName(),
                            R.layout.widget_pending_placeholder);
                    views.setTextViewText(R.id.widget_pending_count, String.valueOf(finalCount));
                    appWidgetManager.updateAppWidget(id, views);
                }
            });
        });
    }
}
