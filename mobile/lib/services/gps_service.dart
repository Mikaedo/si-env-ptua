import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';

class GpsService {
  static Future<bool> requestPermission() async {
    var locationStatus = await Permission.location.status;
    if (locationStatus.isGranted) return true;
    if (locationStatus.isDenied || locationStatus.isRestricted) {
      locationStatus = await Permission.location.request();
    }
    if (locationStatus.isPermanentlyDenied) {
      await openAppSettings();
    }
    return locationStatus.isGranted;
  }

  static Future<bool> requestCameraPermission() async {
    var cameraStatus = await Permission.camera.status;
    if (cameraStatus.isGranted) return true;
    cameraStatus = await Permission.camera.request();
    return cameraStatus.isGranted;
  }

  static Future<Position?> getCurrentPosition() async {
    final hasPermission = await requestPermission();
    if (!hasPermission) return null;

    var serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      serviceEnabled = await Geolocator.openLocationSettings();
      if (!serviceEnabled) return null;
      await Future.delayed(const Duration(seconds: 3));
    }

    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 15),
        ),
      );
    } catch (_) {
      try {
        return await Geolocator.getLastKnownPosition();
      } catch (_) {
        return null;
      }
    }
  }
}
