# GitHub Pages で公開する手順

## 1. GitHub でリポジトリを作る

1. https://github.com にログイン（アカウントがなければ作成）
2. 右上の「+」→「New repository」
3. リポジトリ名を入力（例: `expedition-map`）
4. Public を選択 →「Create repository」

## 2. このフォルダを Git でプッシュする

**初回だけ**、以下のコマンドを実行します。  
（PowerShell または コマンドプロンプトで、このフォルダ `_遠征システム` を開いて実行）

```powershell
cd "c:\corsor\_遠征システム"

git init
git add index.html .nojekyll 遠征計画_座標マップ.html 遠征計画_座標別一覧.html
git commit -m "遠征計画マップ・一覧を追加"
git branch -M main
git remote add origin https://github.com/TetuPalomydes/dam-map.git
git push -u origin main
```

- **【あなたのユーザー名】** … GitHub のユーザー名
- **【リポジトリ名】** … さきほど作ったリポジトリ名（例: `expedition-map`）

プッシュ時に GitHub のユーザー名とパスワード（または Personal Access Token）を聞かれたら入力します。

## 3. GitHub Pages を有効にする

1. GitHub のリポジトリページを開く
2. 「Settings」→ 左メニュー「Pages」
3. 「Source」で **Deploy from a branch** を選ぶ
4. 「Branch」で **main**、フォルダで **/ (root)** を選ぶ → **Save**
5. 数分待つと「Your site is live at https://〇〇.github.io/リポジトリ名/」と表示される

## 4. 見る

- トップ: `https://【ユーザー名】.github.io/【リポジトリ名】/`
- 座標マップ: `https://【ユーザー名】.github.io/【リポジトリ名】/遠征計画_座標マップ.html`
- 座標別一覧: `https://【ユーザー名】.github.io/【リポジトリ名】/遠征計画_座標別一覧.html`

この URL を共有すれば、同じリンクで誰でも閲覧できます。

---

## 更新するとき

マップや一覧を再生成したあと、同じフォルダで:

```powershell
git add 遠征計画_座標マップ.html 遠征計画_座標別一覧.html
git commit -m "マップ・一覧を更新"
git push
```

数分でサイトに反映されます。
