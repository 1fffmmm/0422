// FirebaseのSDKを読み込む（バージョンを main.html と同じ 10.8.1 に統一）
importScripts('https://www.gstatic.com/firebasejs/10.8.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.1/firebase-messaging-compat.js');

// 初期化
firebase.initializeApp({
    apiKey: "AIzaSyBCwEb0nAynWlcIYloAwwdDQocXgD1W8DQ",
    authDomain: "user-cd2c1.firebaseapp.com",
    projectId: "user-cd2c1",
    storageBucket: "user-cd2c1.firebasestorage.app",
    messagingSenderId: "990277200920",
    appId: "1:990277200920:web:952d974484fa76ed89e76d"
}); // ← ★ここの「)」が抜けていました！

const messaging = firebase.messaging();

// バックグラウンドでの通知受け取り
messaging.onBackgroundMessage(function(payload) {
  console.log('バックグラウンド通知を受信:', payload);
  
  // payload.notification が無い場合（dataのみの場合）への対策
  const notificationTitle = payload.notification?.title || "監視アラート";
  const notificationOptions = {
    body: payload.notification?.body || "新着メッセージがあります",
    icon: '/icon-192.png', // manifest.jsonで設定したアイコンなど
    badge: '/icon-192.png'
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});
