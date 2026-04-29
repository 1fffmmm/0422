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
});

const messaging = firebase.messaging();

// バックグラウンドでの通知受け取り
messaging.onBackgroundMessage(function(payload) {
  console.log('バックグラウンド通知を受信:', payload);
  
  // サーバー（notifier.py）側で「notification」ペイロードをセットして送信しているため、
  // バックグラウンド時はブラウザ・OS側が自動的に通知を表示してくれます。
  // そのため、ここでは self.registration.showNotification() による手動表示は行いません（2重通知防止）。
});
