importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "...",
  // index.htmlと同じ設定をここに貼る
});

const messaging = firebase.messaging();

// バックグラウンド通知の受信設定
messaging.onBackgroundMessage((payload) => {
  console.log('通知を受信:', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/icon.png'
  };
  self.registration.showNotification(notificationTitle, notificationOptions);
});

