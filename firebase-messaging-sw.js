importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "...",
  messagingSenderId: "...",
  appId: "...",
  projectId: "..."
});

const messaging = firebase.messaging();
