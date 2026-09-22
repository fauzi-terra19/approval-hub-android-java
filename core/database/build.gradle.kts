plugins {
    alias(libs.plugins.android.library)
}

android {
    namespace = "com.fauzi.wings.core.database"
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
    api(project(":core:model"))
    implementation(project(":domain"))
    api(libs.androidx.room.runtime)
    api(libs.androidx.lifecycle.livedata)
    annotationProcessor(libs.androidx.room.compiler)
}
