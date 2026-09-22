pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "WingsApprovalHub"

include(
    ":app",
    ":core:model",
    ":core:common",
    ":core:ui",
    ":core:database",
    ":core:preference",
    ":core:network",
    ":core:notification",
    ":domain",
    ":data",
    ":feature:auth",
    ":feature:dashboard",
    ":feature:inbox",
    ":feature:request",
    ":feature:analytics",
    ":feature:audit",
    ":feature:settings",
    ":feature:widget"
)
