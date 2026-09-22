plugins {
    alias(libs.plugins.android.library)
}

android {
    namespace = "com.fauzi.wings.core.ui"
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

    buildFeatures {
        dataBinding = true
    }
}

dependencies {
    api(project(":core:model"))
    api(project(":core:common"))
    api(project(":domain"))
    api(libs.androidx.appcompat)
    api(libs.material)
    api(libs.androidx.constraintlayout)
    api(libs.androidx.recyclerview)
    api(libs.androidx.fragment)
    api(libs.androidx.lifecycle.livedata)
    api(libs.androidx.lifecycle.viewmodel)
    api(libs.androidx.navigation.fragment)
    api(libs.androidx.navigation.ui)
}
