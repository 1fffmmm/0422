// FirebaseのSDKを読み込む
importScripts('https://www.gstatic.com/firebasejs/10.x.x/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.x.x/firebase-messaging-compat.js');

// 初期化（main.htmlと同じ設定が必要）
firebase.initializeApp({
apiKey: "AIzaSyBCwEb0nAynWlcIYloAwwdDQocXgD1W8DQ",
    authDomain: "user-cd2c1.firebaseapp.com",
    projectId: "user-cd2c1",
    storageBucket: "user-cd2c1.firebasestorage.app",
    messagingSenderId: "990277200920",
    appId: "1:990277200920:web:952d974484fa76ed89e76d"
};


const messaging = firebase.messaging();

// バックグラウンドでの通知受け取り
messaging.onBackgroundMessage(function(payload) {
  console.log('バックグラウンド通知を受信:', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
  };
  self.registration.showNotification(notificationTitle, notificationOptions);
});

