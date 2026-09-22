# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

ROOT = Path(r"D:/fauzi/cursor/wings/android")
base = runpy.run_path(str(ROOT / "tools" / "gen_part1.py"))
w = base["w"]
android_lib = base["android_lib"]
empty_manifest = base["empty_manifest"]


def gen_database_gradle():
    w(
        "core/database/build.gradle.kts",
        android_lib(
            "com.fauzi.wings.core.database",
            [
                'api(project(":core:model"))',
                'implementation(project(":domain"))',
                "api(libs.androidx.room.runtime)",
                "annotationProcessor(libs.androidx.room.compiler)",
                "api(libs.androidx.lifecycle.livedata)",
            ],
        ),
    )
    w("core/database/consumer-rules.pro", "#\n")
    w("core/database/src/main/AndroidManifest.xml", empty_manifest())


if __name__ == "__main__":
    gen_database_gradle()
    print("db gradle ok")
