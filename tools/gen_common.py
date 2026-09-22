# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(r"D:/fauzi/cursor/wings/android")


def w(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if content.startswith("\n"):
        content = content[1:]
    p.write_text(content, encoding="utf-8")
    print(rel)


def android_lib(ns, deps, databinding=False):
    bf = ""
    if databinding:
        bf = """
    buildFeatures {
        dataBinding = true
        viewBinding = true
    }
"""
    dep = "\n".join("    " + d for d in deps)
    return f"""plugins {{
    alias(libs.plugins.android.library)
}}

android {{
    namespace = "{ns}"
    compileSdk = libs.versions.compileSdk.get().toInt()
    defaultConfig {{
        minSdk = libs.versions.minSdk.get().toInt()
        consumerProguardFiles("consumer-rules.pro")
    }}
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
{bf}}}

dependencies {{
{dep}
}}
"""


def empty_manifest():
    return '<?xml version="1.0" encoding="utf-8"?>\n<manifest />\n'


def gen_common():
    w("core/common/build.gradle.kts", android_lib("com.fauzi.wings.core.common", [
        'api(project(":core:model"))',
        "implementation(libs.androidx.annotation)",
    ]))
    w("core/common/consumer-rules.pro", "#\n")
    w("core/common/src/main/AndroidManifest.xml", empty_manifest())
    w(
        "core/common/src/main/java/com/fauzi/wings/core/common/MoneyFormat.java",
        """package com.fauzi.wings.core.common;

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
""",
    )
    w(
        "core/common/src/main/java/com/fauzi/wings/core/common/DateFormatters.java",
        """package com.fauzi.wings.core.common;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class DateFormatters {
    private static final SimpleDateFormat FULL =
            new SimpleDateFormat("dd MMM yyyy HH:mm", new Locale("in", "ID"));
    private DateFormatters() {}
    public static String full(long epoch) { return FULL.format(new Date(epoch)); }
}
""",
    )


if __name__ == "__main__":
    gen_common()
    print("OK common")
