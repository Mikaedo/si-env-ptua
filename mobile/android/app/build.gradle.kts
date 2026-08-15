plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "ci.ageroute.si_env"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "ci.ageroute.si_env"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the debug keys for now, so `flutter run --release` works.
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    // ── Deux applications issues d'un meme socle ──────────────────────────
    //
    // Les agents de l'AGEROUTE et les riverains des chantiers ne relevent ni
    // du meme public, ni du meme canal de distribution : l'application des
    // agents se deploie en interne, celle des riverains a vocation a etre
    // telechargee librement. Elles ne suivent donc pas le meme rythme de mise
    // a jour et ne peuvent pas partager un identifiant applicatif.
    //
    // Les variantes de production Android repondent exactement a ce besoin :
    // un depot unique, un socle de code commun (service d'API, modeles,
    // theme, geolocalisation, appareil photo, synchronisation hors ligne),
    // et deux paquets installables cote a cote sur un meme telephone. Seuls
    // le point d'entree et la coque de navigation different.
    flavorDimensions += "public"

    productFlavors {
        create("agent") {
            dimension = "public"
            // Identifiant historique conserve : les installations existantes
            // continuent de recevoir les mises a jour sans reinstallation.
            applicationId = "ci.ageroute.si_env"
            resValue("string", "app_name", "SI-ENV")
        }
        create("citoyen") {
            dimension = "public"
            applicationId = "ci.ageroute.si_env.citoyen"
            resValue("string", "app_name", "SI-ENV Citoyen")
        }
    }
}

flutter {
    source = "../.."
}
