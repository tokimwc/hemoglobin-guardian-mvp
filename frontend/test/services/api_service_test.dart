import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:hemoglobin_guardian/src/services/api_service.dart';

@GenerateMocks([ApiService])
void main() {
  group('ApiService Tests', () {
    late ApiService apiService;

    setUp(() {
      apiService = ApiService();
    });

    test('analyzeImage returns expected response', () async {
      final testImage = File('test_assets/test_image.jpg');
      final response = await apiService.analyzeImage(testImage);
      expect(response, isA<Map<String, dynamic>>());
    });
  });
} 