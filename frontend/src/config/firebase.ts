import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: "shecares-a6575.firebaseapp.com",
  projectId: "shecares-a6575",
  storageBucket: "shecares-a6575.firebasestorage.app",
  messagingSenderId: "47603653504",
  appId: "1:47603653504:web:7378a54fd969d06258bf65"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export default app;