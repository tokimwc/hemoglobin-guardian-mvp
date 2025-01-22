import 'dart:io';
import 'package:path/path.dart' as path;

class TestConfig {
  static String get testAssetsPath => path.join(Directory.current.path, 'test_assets');
  
  static String get testImagePath => path.join(testAssetsPath, 'test_image.jpg');
  
  static Future<void> ensureTestAssets() async {
    final testAssetsDir = Directory(testAssetsPath);
    if (!await testAssetsDir.exists()) {
      await testAssetsDir.create(recursive: true);
    }
  }
  
  static Future<bool> validateTestImage() async {
    final testImage = File(testImagePath);
    return testImage.exists();
  }
} 