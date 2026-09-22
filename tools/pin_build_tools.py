from pathlib import Path

root = Path(r"D:\fauzi\cursor\wings\android")
old = "compileSdk = libs.versions.compileSdk.get().toInt()"
new = old + '\n    buildToolsVersion = "35.0.0"'
for p in root.rglob("build.gradle.kts"):
    if "tools" in p.parts:
        continue
    t = p.read_text(encoding="utf-8")
    if "compileSdk" in t and "buildToolsVersion" not in t:
        p.write_text(t.replace(old, new), encoding="utf-8")
        print("patched", p.relative_to(root))
