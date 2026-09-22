plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.fauzi.wings.app"
    compileSdk = libs.versions.compileSdk.get().toInt()
    buildToolsVersion = "35.0.0"

    defaultConfig {
        applicationId = "com.fauzi.wings"
        minSdk = libs.versions.minSdk.get().toInt()
        targetSdk = libs.versions.targetSdk.get().toInt()
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        dataBinding = true
        viewBinding = true
    }
}

dependencies {
    implementation(project(":core:ui"))
    implementation(project(":core:model"))
    implementation(project(":core:common"))
    implementation(project(":core:database"))
    implementation(project(":core:preference"))
    implementation(project(":core:network"))
    implementation(project(":core:notification"))
    implementation(project(":domain"))
    implementation(project(":data"))
    implementation(project(":feature:auth"))
    implementation(project(":feature:dashboard"))
    implementation(project(":feature:inbox"))
    implementation(project(":feature:request"))
    implementation(project(":feature:analytics"))
    implementation(project(":feature:audit"))
    implementation(project(":feature:settings"))
    implementation(project(":feature:widget"))

    implementation(libs.androidx.core)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.fragment)
    implementation(libs.androidx.navigation.fragment)
    implementation(libs.androidx.navigation.ui)
    implementation(libs.androidx.lifecycle.runtime)
    implementation(libs.androidx.lifecycle.viewmodel)
    implementation(libs.androidx.lifecycle.livedata)
    implementation(libs.androidx.work)
}
