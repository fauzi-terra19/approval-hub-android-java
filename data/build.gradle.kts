plugins {
    alias(libs.plugins.android.library)
}

android {
    namespace = "com.fauzi.wings.data"
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
    api(project(":domain"))
    api(project(":core:model"))
    api(project(":core:common"))
    api(project(":core:database"))
    api(project(":core:preference"))
    api(project(":core:network"))
    api(project(":core:notification"))
    api(libs.androidx.lifecycle.livedata)
    api(libs.androidx.lifecycle.viewmodel)
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.core)
}
