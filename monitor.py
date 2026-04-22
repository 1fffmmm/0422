def check_keywords_and_notify(drive_text):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # 接続情報のデバッグ表示（最初の数文字だけ表示して確認）
    print(f"DEBUG: Connecting to {url}")
    if key:
        print(f"DEBUG: API Key exists (Length: {len(key)})")

    try:
        supabase = create_client(url, key)
        
        # .execute() の結果を直接確認
        response = supabase.table("keywords").select("word").execute()
        
        print(f"DEBUG: Full Response: {response}")

        if not response.data:
            print("【警告】Supabaseからデータが取得できませんでした（0件）。")
            # テーブルの中身を全部取得してみるテスト
            test_res = supabase.table("keywords").select("*").execute()
            print(f"DEBUG: All columns test: {test_res.data}")
            return

        keywords = [item['word'] for item in response.data]
        print(f"監視中のキーワード: {keywords}")

        found_keywords = [word for word in keywords if word in drive_text]
        if found_keywords:
            print(f"【一致あり】見つかった文字: {found_keywords}")
        else:
            print("一致する文字はありませんでした。")
            
    except Exception as e:
        print(f"ERROR: Supabase連携中に例外が発生しました: {e}")
