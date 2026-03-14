/**
 * Firebase client SDK setup for the web app.
 * Initializes the Firebase app and exposes auth for sign-in, sign-out, and token verification.
 */
import { initializeApp, getApps, FirebaseApp } from "firebase/app";
import { getAuth } from "firebase/auth";

/** Shape of the Firebase web app config (from Firebase Console). */
interface FirebaseConfig {
    apiKey: string;
    authDomain: string;
    projectId: string;
    storageBucket: string;
    messagingSenderId: string;
    appId: string;
}

/** Returns Firebase config from env vars if apiKey and projectId are present; otherwise null. */
function getFirebaseConfig(): FirebaseConfig | null {
  const config = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  };
  if (!config.apiKey || !config.projectId) return null;
  return config as FirebaseConfig;
}

/**
 * Returns the Firebase app instance. Uses getApps() to avoid initializing twice
 * (e.g. during Next.js hot reload), which would throw an error.
 */
const getFirebaseApp = (): FirebaseApp | null => {
  if (getApps().length === 0) {
    const config = getFirebaseConfig();
    if (!config) {
      console.warn("Firebase config missing. Check NEXT_PUBLIC_FIREBASE_* env vars.");
      return null;
    }
    return initializeApp(config);
  }
  return getApps()[0] as FirebaseApp;
};

/** Firebase app instance (null if config is missing). */
export const app = getFirebaseApp();
/** Auth instance for sign-in, sign-out, onAuthStateChanged, etc. Null if app failed to initialize. */
export const auth = app ? getAuth(app) : null;