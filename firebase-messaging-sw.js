// firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

firebase.initializeApp({
 apiKey: "AIzaSyBCwEb0nAynWlcIYloAwwdDQocXgD1W8DQ",
  authDomain: "user-cd2c1.firebaseapp.com",
  projectId: "user-cd2c1",
  storageBucket: "user-cd2c1.firebasestorage.app",
  messagingSenderId: "990277200920",
  appId: "1:990277200920:web:952d974484fa76ed89e76d",
});

const messaging = firebase.messaging();
