plugins {
    alias(libs.plugins.android.library)
}

android {
    namespace = "com.fauzi.wings.core.notification"
    compileSdk = libs.versions.compileSdk.get().toInt()
    buildToolsVersion = "35.0.0"

    defaultConfig {
        minSdk = libs.versions.minSdk.get().toInt()
        consumerProguardFiles("consumer-rules.pro")
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(libs.androidx.core)
    implementation(libs.androidx.appcompat)
}
