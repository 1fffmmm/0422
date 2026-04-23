self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : { title: '通知', body: '新着メッセージがあります' };
    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: 'https://cdn-icons-png.flaticon.com/512/1827/1827349.png'
        })
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/')
    );
});
