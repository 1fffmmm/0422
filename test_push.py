<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>通知管理システム</title>
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <style>
    body { font-family: -apple-system, sans-serif; padding: 20px; max-width: 500px; margin: auto; background-color: #f9f9f9; line-height: 1.6; }
    .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    h2, h3 { margin-top: 0; color: #333; font-size: 1.2em; }
    .btn-insta { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-bottom: 20px; }
    .keyword-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; }
    .delete-btn { color: #ff4d4d; border: 1px solid #ff4d4d; background: none; border-radius: 4px; padding: 4px 10px; cursor: pointer; font-size: 0.8em; }
    .input-group { display: flex; gap: 8px; margin-top: 15px; }
    input[type="text"] { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
    .add-btn { padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; }
    #analysis-content { white-space: pre-wrap; background: #f0f0f0; padding: 12px; border-radius: 6px; font-size: 0.9em; min-height: 50px; }
    
    /* 通知スイッチ */
    .switch-container { display: flex; align-items: center; justify-content: space-between; }
    .switch { position: relative; display: inline-block; width: 50px; height: 28px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 28px; }
    .slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
    input:checked + .slider { background-color: #34c759; }
    input:checked + .slider:before { transform: translateX(22px); }
  </style>
</head>
<body>

  <a href="https://www.instagram.com/stories/jr_official_/" target="_blank" class="btn-insta">
    Instagramストーリーを確認
  </a>

  <div class="card">
    <div class="switch-container">
      <h2>プッシュ通知を受け取る</h2>
      <label class="switch">
        <input type="checkbox" id="push-switch">
        <span class="slider"></span>
      </label>
    </div>
    <p id="push-status" style="font-size: 0.8em; color: #666; margin-top: 10px;">状態を確認中...</p>
  </div>

  <div class="card">
    <h3>最新の解析結果</h3>
    <div id="analysis-content">読み込み中...</div>
  </div>

  <div class="card">
    <h3>監視キーワード (最大10個)</h3>
    <div id="keyword-list">読み込み中...</div>
    <div class="input-group">
      <input type="text" id="new-keyword" placeholder="例: 公演, チケット">
      <button class="add-btn" onclick="addKeyword()">追加</button>
    </div>
  </div>

  <script>
    // --- 1. 設定情報 ---
    const SUPABASE_URL = "https://ltqqmclfgdxtasvtirtf.supabase.co";
    const SUPABASE_KEY = "sb_publishable_iPDG85-2s9n0TBw-kVs55g_xC3ZSt-H"; // あなたのAnon Key
    const VAPID_PUBLIC_KEY = "BPjCNf2epwHU2U_a4X6d2zEfDzqRvmFYmXJrY2zUMR-h62JZG8bJ2Y5sXr0VaZp_XSaUkn0p3TH3X0_SCoD9p5A"; // あなたの公開鍵
    
    const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

    // --- 2. WebPush通知関連のロジック ---
    const pushSwitch = document.getElementById('push-switch');
    const statusText = document.getElementById('push-status');

    // URLセーフなBase64をUint8Arrayに変換する関数
    function urlBase64ToUint8Array(base64String) {
      const padding = '='.repeat((4 - base64String.length % 4) % 4);
      const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
      const rawData = window.atob(base64);
      const outputArray = new Uint8Array(rawData.length);
      for (let i = 0; i < rawData.length; ++i) { outputArray[i] = rawData.charCodeAt(i); }
      return outputArray;
    }

    // ページ読み込み時に購読状態を確認
    async function checkSubscription() {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        statusText.innerText = "このブラウザは通知に対応していません。";
        pushSwitch.disabled = true;
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      
      pushSwitch.checked = !!subscription;
      statusText.innerText = subscription ? "通知は有効です" : "通知は無効です";
    }

    // 通知をオンにする（購読開始）
    async function subscribeUser() {
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
        });

        // Supabaseの subscriptions テーブルに保存
        const { error } = await supabaseClient
          .from('subscriptions')
          .upsert([{ 
            endpoint: subscription.endpoint, 
            auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('auth')))),
            p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('p256dh'))))
          }]);

        if (error) throw error;
        statusText.innerText = "通知をオンにしました";
      } catch (err) {
        console.error("購読失敗:", err);
        pushSwitch.checked = false;
        alert("通知の許可に失敗しました。Safariの設定を確認してください。");
      }
    }

    // 通知をオフにする（購読解除）
    async function unsubscribeUser() {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await subscription.unsubscribe();
        // DBから削除
        await supabaseClient.from('subscriptions').delete().eq('endpoint', subscription.endpoint);
      }
      statusText.innerText = "通知をオフにしました";
    }

    pushSwitch.addEventListener('change', () => {
      if (pushSwitch.checked) subscribeUser();
      else unsubscribeUser();
    });

    // --- 3. キーワード・解析結果管理 ---
    async function fetchKeywords() {
      const { data, error } = await supabaseClient.from('keywords').select('*').order('created_at', { ascending: true });
      if (error) return;
      document.getElementById('keyword-list').innerHTML = data.map(k => `
        <div class="keyword-item">
          <span>${k.word}</span>
          <button class="delete-btn" onclick="deleteKeyword(${k.id})">削除</button>
        </div>
      `).join('');
      window.currentKeywordCount = data.length;
    }

    async function addKeyword() {
      const input = document.getElementById('new-keyword');
      const word = input.value.trim();
      if (!word || window.currentKeywordCount >= 10) return;
      await supabaseClient.from('keywords').insert([{ word: word }]);
      input.value = '';
      fetchKeywords();
    }

    async function deleteKeyword(id) {
      await supabaseClient.from('keywords').delete().eq('id', id);
      fetchKeywords();
    }

    async function fetchAnalysisResults() {
      const { data } = await supabaseClient.from('analysis_logs').select('content').order('updated_at', { ascending: false }).limit(1).single();
      document.getElementById('analysis-content').innerText = data ? data.content : "データなし";
    }

    // Service Workerの登録
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js');
    }

    // 初期化
    checkSubscription();
    fetchKeywords();
    fetchAnalysisResults();
  </script>
</body>
</html>
