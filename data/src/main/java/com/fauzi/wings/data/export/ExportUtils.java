package com.fauzi.wings.data.export;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.net.Uri;

import androidx.core.content.FileProvider;

import com.fauzi.wings.core.model.ApprovalAction;
import com.fauzi.wings.core.model.ApprovalRequest;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class ExportUtils {
    private static final SimpleDateFormat SDF =
            new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault());

    private ExportUtils() {}

    public static Uri exportAuditCsv(
            Context context,
            List<ApprovalRequest> requests,
            List<ApprovalAction> actions,
            Map<Long, String> userNames
    ) throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("requestId,title,status,type,amount,department,actionId,level,decision,actor,comment,createdAt\n");
        Map<Long, List<ApprovalAction>> byReq = new HashMap<>();
        for (ApprovalAction a : actions) {
            byReq.computeIfAbsent(a.requestId, k -> new ArrayList<>()).add(a);
        }
        for (ApprovalRequest req : requests) {
            List<ApprovalAction> rows = byReq.getOrDefault(req.id, new ArrayList<>());
            if (rows.isEmpty()) {
                sb.append(req.id).append(",\"").append(esc(req.title)).append("\",")
                        .append(req.status).append(',').append(req.type).append(',')
                        .append(req.amount).append(',').append(req.department)
                        .append(",,,,,,\n");
            } else {
                for (ApprovalAction a : rows) {
                    String actor = userNames.containsKey(a.actorId)
                            ? userNames.get(a.actorId) : String.valueOf(a.actorId);
                    sb.append(req.id).append(",\"").append(esc(req.title)).append("\",")
                            .append(req.status).append(',').append(req.type).append(',')
                            .append(req.amount).append(',').append(req.department).append(',')
                            .append(a.id).append(',').append(a.level).append(',')
                            .append(a.decision).append(",\"").append(esc(actor)).append("\",\"")
                            .append(esc(a.comment)).append("\",")
                            .append(SDF.format(new Date(a.createdAt))).append('\n');
                }
            }
        }
        File file = new File(context.getCacheDir(), "audit_" + System.currentTimeMillis() + ".csv");
        try (OutputStreamWriter writer = new OutputStreamWriter(
                new FileOutputStream(file), StandardCharsets.UTF_8)) {
            writer.write(sb.toString());
        }
        return FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
    }

    public static Uri exportAuditPdf(
            Context context,
            List<ApprovalRequest> requests,
            List<ApprovalAction> actions,
            Map<Long, String> userNames
    ) throws Exception {
        PdfDocument doc = new PdfDocument();
        Paint paint = new Paint();
        paint.setTextSize(10f);
        int pageNumber = 1;
        float y = 40f;
        PdfDocument.Page page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
        Canvas canvas = page.getCanvas();
        canvas.drawText("ApprovalHub Audit Trail", 40f, y, paint);
        y += 24f;

        int limit = Math.min(40, requests.size());
        for (int i = 0; i < limit; i++) {
            ApprovalRequest req = requests.get(i);
            if (y + 60f > 800f) {
                doc.finishPage(page);
                pageNumber++;
                page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
                canvas = page.getCanvas();
                y = 40f;
            }
            canvas.drawText("#" + req.id + " " + req.title + " [" + req.status + "]", 40f, y, paint);
            y += 14f;
            canvas.drawText(req.type + " · " + req.amount + " · " + req.department, 48f, y, paint);
            y += 14f;
            for (ApprovalAction a : actions) {
                if (a.requestId != req.id) continue;
                if (y + 16f > 800f) {
                    doc.finishPage(page);
                    pageNumber++;
                    page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
                    canvas = page.getCanvas();
                    y = 40f;
                }
                String actor = userNames.containsKey(a.actorId)
                        ? userNames.get(a.actorId) : String.valueOf(a.actorId);
                canvas.drawText("L" + a.level + " " + a.decision + " by " + actor
                        + " - " + a.comment, 56f, y, paint);
                y += 14f;
            }
            y += 8f;
        }
        doc.finishPage(page);
        File file = new File(context.getCacheDir(), "audit_" + System.currentTimeMillis() + ".pdf");
        try (FileOutputStream fos = new FileOutputStream(file)) {
            doc.writeTo(fos);
        }
        doc.close();
        return FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
    }

    public static void shareUri(Context context, Uri uri, String mime, String title) {
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType(mime);
        intent.putExtra(Intent.EXTRA_STREAM, uri);
        intent.putExtra(Intent.EXTRA_SUBJECT, title);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        Intent chooser = Intent.createChooser(intent, title);
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(chooser);
    }

    public static void shareBitmap(Context context, Bitmap bitmap, String title) throws Exception {
        File file = new File(context.getCacheDir(), "chart_" + System.currentTimeMillis() + ".png");
        try (FileOutputStream fos = new FileOutputStream(file)) {
            bitmap.compress(Bitmap.CompressFormat.PNG, 95, fos);
        }
        Uri uri = FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
        shareUri(context, uri, "image/png", title);
    }

    public static Bitmap createSimpleChartBitmap(List<String> labels, List<Float> values, String title) {
        int width = 1080;
        int height = 720;
        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bitmap);
        canvas.drawColor(0xFFFFFFFF);
        Paint titlePaint = new Paint();
        titlePaint.setTextSize(42f);
        titlePaint.setFakeBoldText(true);
        titlePaint.setColor(0xFF0F4C5C);
        Paint barPaint = new Paint();
        barPaint.setColor(0xFF2A9D8F);
        Paint textPaint = new Paint();
        textPaint.setTextSize(28f);
        textPaint.setColor(0xFF333333);
        canvas.drawText(title, 40f, 60f, titlePaint);
        float max = 1f;
        for (Float v : values) {
            if (v != null && v > max) max = v;
        }
        float chartTop = 120f;
        float chartBottom = height - 100f;
        float chartHeight = chartBottom - chartTop;
        float slot = (width - 80f) / Math.max(1, values.size());
        for (int i = 0; i < values.size(); i++) {
            float v = values.get(i) == null ? 0f : values.get(i);
            float barH = (v / max) * chartHeight;
            float left = 40f + i * slot + slot * 0.2f;
            float right = left + slot * 0.6f;
            canvas.drawRect(left, chartBottom - barH, right, chartBottom, barPaint);
            String label = i < labels.size() ? labels.get(i) : "";
            if (label.length() > 8) label = label.substring(0, 8);
            canvas.drawText(label, left, chartBottom + 40f, textPaint);
        }
        return bitmap;
    }

    private static String esc(String value) {
        return value == null ? "" : value.replace("\"", "'");
    }
}
