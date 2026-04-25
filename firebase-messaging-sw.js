// firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/10.8.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.1/firebase-messaging-compat.js');

const firebaseConfig = {
    apiKey: "AIzaSyBCwEb0nAynWlcIYloAwwdDQocXgD1W8DQ",
    authDomain: "user-cd2c1.firebaseapp.com",
    projectId: "user-cd2c1",
    storageBucket: "user-cd2c1.firebasestorage.app",
    messagingSenderId: "990277200920",
    appId: "1:990277200920:web:952d974484fa76ed89e76d"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// バックグラウンドでのプッシュ通知処理
messaging.onBackgroundMessage((payload) => {
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/icon.png' // 通知アイコンのパスがあれば指定
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
