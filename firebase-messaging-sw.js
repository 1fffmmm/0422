importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// main.htmlと同じFirebase設定
firebase.initializeApp({
  apiKey: "AIzaSyBCwEb0nAynWlcIYloAwwdDQocXgD1W8DQ",
  authDomain: "user-cd2c1.firebaseapp.com",
  projectId: "user-cd2c1",
  storageBucket: "user-cd2c1.firebasestorage.app",
  messagingSenderId: "990277200920",
  appId: "1:990277200920:web:952d974484fa76ed89e76d"
});

const messaging = firebase.messaging();

// バックグラウンドで通知を受け取った時の処理
messaging.onBackgroundMessage((payload) => {
  console.log('バックグラウンド通知を受信:', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/icon.png' // アイコンがあれば指定
  };
  self.registration.showNotification(notificationTitle, notificationOptions);
});
