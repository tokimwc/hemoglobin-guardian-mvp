import 'package:mockito/annotations.dart';
import 'package:hemoglobin_guardian/src/services/api_service.dart';
import 'package:hemoglobin_guardian/src/services/image_service.dart';
import 'package:hemoglobin_guardian/src/services/auth_service.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:image_picker/image_picker.dart';

@GenerateMocks([
  ApiService,
  ImageService,
  AuthService,
  FirebaseAuth,
  ImagePicker,
])
void main() {} 