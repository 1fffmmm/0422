// 通知を受け取った時の処理
self.addEventListener('push', function(event) {
    const data = event.data ? event.data.json() : { title: '通知', body: '新着メッセージがあります' };
    
    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: 'icon.png' // アイコンがあれば
        })
    );
});

// 通知をクリックした時の処理
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/') // 通知をクリックしたらサイトを開く
    );
});
