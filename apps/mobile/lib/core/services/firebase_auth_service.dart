import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

/// Result of a social sign-in attempt
class SocialSignInResult {
  final bool success;
  final String? email;
  final String? displayName;
  final String? photoUrl;
  final String? firebaseIdToken;
  final String? error;
  final String provider; // 'google', 'apple', 'guest'

  SocialSignInResult({
    required this.success,
    this.email,
    this.displayName,
    this.photoUrl,
    this.firebaseIdToken,
    this.error,
    required this.provider,
  });
}

/// Service for handling Firebase Authentication with social providers
class FirebaseAuthService {
  FirebaseAuth? _firebaseAuth;
  GoogleSignIn? _googleSignIn;
  bool _isAvailable = false;

  FirebaseAuthService() {
    _initialize();
  }

  void _initialize() {
    try {
      _firebaseAuth = FirebaseAuth.instance;
      _googleSignIn = GoogleSignIn(scopes: ['email', 'profile']);
      _isAvailable = true;
    } catch (e) {
      // Firebase not configured
      _isAvailable = false;
      debugPrint('FirebaseAuthService: Firebase not available');
    }
  }

  /// Check if Firebase is available
  bool get isAvailable => _isAvailable;

  /// Sign in with Google
  Future<SocialSignInResult> signInWithGoogle() async {
    if (!_isAvailable || _googleSignIn == null || _firebaseAuth == null) {
      return SocialSignInResult(
        success: false,
        error: 'Google Sign-In no está disponible. Usa email/contraseña.',
        provider: 'google',
      );
    }

    try {
      // Trigger the authentication flow
      final GoogleSignInAccount? googleUser = await _googleSignIn!.signIn();

      if (googleUser == null) {
        // User cancelled the sign-in
        return SocialSignInResult(
          success: false,
          error: 'Inicio de sesión cancelado',
          provider: 'google',
        );
      }

      // Obtain the auth details from the request
      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;

      // Create a new credential
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Sign in to Firebase with the Google credential
      final UserCredential userCredential = await _firebaseAuth!.signInWithCredential(credential);
      final User? user = userCredential.user;

      if (user == null) {
        return SocialSignInResult(
          success: false,
          error: 'Error al obtener usuario de Firebase',
          provider: 'google',
        );
      }

      // Get the Firebase ID token to send to backend
      final String? idToken = await user.getIdToken();

      return SocialSignInResult(
        success: true,
        email: user.email,
        displayName: user.displayName ?? googleUser.displayName,
        photoUrl: user.photoURL ?? googleUser.photoUrl,
        firebaseIdToken: idToken,
        provider: 'google',
      );
    } on FirebaseAuthException catch (e) {
      return SocialSignInResult(
        success: false,
        error: _getFirebaseErrorMessage(e.code),
        provider: 'google',
      );
    } catch (e) {
      return SocialSignInResult(
        success: false,
        error: 'Error de conexión. Intenta de nuevo.',
        provider: 'google',
      );
    }
  }

  /// Sign in with Apple
  Future<SocialSignInResult> signInWithApple() async {
    if (!_isAvailable || _firebaseAuth == null) {
      return SocialSignInResult(
        success: false,
        error: 'Apple Sign-In no está disponible. Usa email/contraseña.',
        provider: 'apple',
      );
    }

    try {
      // Generate nonce for security
      final rawNonce = _generateNonce();
      final nonce = _sha256ofString(rawNonce);

      // Request credentials from Apple
      final appleCredential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
        nonce: nonce,
      );

      // Create OAuth credential
      final oauthCredential = OAuthProvider('apple.com').credential(
        idToken: appleCredential.identityToken,
        rawNonce: rawNonce,
      );

      // Sign in to Firebase
      final UserCredential userCredential = await _firebaseAuth!.signInWithCredential(oauthCredential);
      final User? user = userCredential.user;

      if (user == null) {
        return SocialSignInResult(
          success: false,
          error: 'Error al obtener usuario de Firebase',
          provider: 'apple',
        );
      }

      // Get the Firebase ID token
      final String? idToken = await user.getIdToken();

      // Apple only provides name on first sign-in
      String? displayName = user.displayName;
      if (displayName == null || displayName.isEmpty) {
        final givenName = appleCredential.givenName ?? '';
        final familyName = appleCredential.familyName ?? '';
        displayName = '$givenName $familyName'.trim();
        if (displayName.isEmpty) {
          displayName = 'Cazador Apple';
        }
      }

      return SocialSignInResult(
        success: true,
        email: user.email ?? appleCredential.email,
        displayName: displayName,
        photoUrl: user.photoURL,
        firebaseIdToken: idToken,
        provider: 'apple',
      );
    } on SignInWithAppleAuthorizationException catch (e) {
      if (e.code == AuthorizationErrorCode.canceled) {
        return SocialSignInResult(
          success: false,
          error: 'Inicio de sesión cancelado',
          provider: 'apple',
        );
      }
      return SocialSignInResult(
        success: false,
        error: 'Error de autorización de Apple',
        provider: 'apple',
      );
    } on FirebaseAuthException catch (e) {
      return SocialSignInResult(
        success: false,
        error: _getFirebaseErrorMessage(e.code),
        provider: 'apple',
      );
    } catch (e) {
      return SocialSignInResult(
        success: false,
        error: 'Error de conexión. Intenta de nuevo.',
        provider: 'apple',
      );
    }
  }

  /// Sign in anonymously (for guest users)
  Future<SocialSignInResult> signInAnonymously() async {
    if (!_isAvailable || _firebaseAuth == null) {
      return SocialSignInResult(
        success: false,
        error: 'Modo invitado no disponible. Usa email/contraseña.',
        provider: 'guest',
      );
    }

    try {
      final UserCredential userCredential = await _firebaseAuth!.signInAnonymously();
      final User? user = userCredential.user;

      if (user == null) {
        return SocialSignInResult(
          success: false,
          error: 'Error al crear cuenta de invitado',
          provider: 'guest',
        );
      }

      final String? idToken = await user.getIdToken();
      final guestId = user.uid.substring(0, 8);

      return SocialSignInResult(
        success: true,
        email: 'guest_$guestId@icfesleveling.app',
        displayName: 'Cazador $guestId',
        firebaseIdToken: idToken,
        provider: 'guest',
      );
    } on FirebaseAuthException catch (e) {
      return SocialSignInResult(
        success: false,
        error: _getFirebaseErrorMessage(e.code),
        provider: 'guest',
      );
    } catch (e) {
      return SocialSignInResult(
        success: false,
        error: 'Error al crear cuenta de invitado',
        provider: 'guest',
      );
    }
  }

  /// Sign out from all providers
  Future<void> signOut() async {
    if (!_isAvailable) return;

    final futures = <Future>[];
    if (_firebaseAuth != null) futures.add(_firebaseAuth!.signOut());
    if (_googleSignIn != null) futures.add(_googleSignIn!.signOut());
    await Future.wait(futures);
  }

  /// Check if user is currently signed in
  bool get isSignedIn => _isAvailable && _firebaseAuth?.currentUser != null;

  /// Get current Firebase user
  User? get currentUser => _firebaseAuth?.currentUser;

  /// Get current Firebase ID token (for backend auth)
  Future<String?> getIdToken() async {
    return await _firebaseAuth?.currentUser?.getIdToken();
  }

  /// Generate a cryptographically secure random nonce
  String _generateNonce([int length = 32]) {
    const charset = '0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._';
    final random = Random.secure();
    return List.generate(length, (_) => charset[random.nextInt(charset.length)]).join();
  }

  /// Returns the sha256 hash of [input] in hex notation.
  String _sha256ofString(String input) {
    final bytes = utf8.encode(input);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  /// Convert Firebase error codes to user-friendly messages
  String _getFirebaseErrorMessage(String code) {
    switch (code) {
      case 'account-exists-with-different-credential':
        return 'Ya existe una cuenta con este email usando otro método de inicio de sesión.';
      case 'invalid-credential':
        return 'Credenciales inválidas. Intenta de nuevo.';
      case 'user-disabled':
        return 'Esta cuenta ha sido deshabilitada.';
      case 'user-not-found':
        return 'No se encontró una cuenta con estas credenciales.';
      case 'wrong-password':
        return 'Contraseña incorrecta.';
      case 'invalid-verification-code':
        return 'Código de verificación inválido.';
      case 'network-request-failed':
        return 'Error de conexión. Verifica tu internet.';
      case 'too-many-requests':
        return 'Demasiados intentos. Espera un momento.';
      case 'operation-not-allowed':
        return 'Este método de inicio de sesión no está habilitado.';
      default:
        return 'Error de autenticación. Intenta de nuevo.';
    }
  }
}

/// Provider for FirebaseAuthService
final firebaseAuthServiceProvider = Provider<FirebaseAuthService>((ref) {
  return FirebaseAuthService();
});

/// Check if Apple Sign-In is available on this device
Future<bool> isAppleSignInAvailable() async {
  if (defaultTargetPlatform == TargetPlatform.iOS) {
    return await SignInWithApple.isAvailable();
  }
  // Apple Sign-In is also available on Android
  // but requires additional setup
  return false;
}
