plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
}

subprojects {
    plugins.withId("com.android.application") {
        extensions.configure<com.android.build.gradle.internal.dsl.BaseAppModuleExtension> {
            buildToolsVersion = "35.0.0"
        }
    }
    plugins.withId("com.android.library") {
        extensions.configure<com.android.build.gradle.LibraryExtension> {
            buildToolsVersion = "35.0.0"
        }
    }
}
