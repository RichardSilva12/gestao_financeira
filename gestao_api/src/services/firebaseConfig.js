

import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDVLRP-6l4xrJkTQQWfwE7YlSkcy1EtGQQ",
  authDomain: "gestao-financeira-1ce39.firebaseapp.com",
  projectId: "gestao-financeira-1ce39",
  storageBucket: "gestao-financeira-1ce39.firebasestorage.app",
  messagingSenderId: "158960630504",
  appId: "1:158960630504:web:a684b34e5cb95952d2675d"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

