# Python Scene Handoff
![Lorenz demo](docs/assets/lorenz-preview.webp)

**Pythonで運動を計算し、DCCで仕上げる。**

Pythonで生成した時間変化する3Dシーンを、標準交換形式を介してクリエイティブDCCへ渡すための小さな実証プロジェクトです。

```text
NumPy / SciPy / simulation / procedural Python
                    ↓
              scene state S(t)
                    ↓
             出力fpsでサンプリング
              ↙                 ↘
      animated glTF             USD
           ↓                     ↓
   After Effects          Resolve / Fusion
```

Manimには依存しません。Manim、SciPy、独自シミュレーション、VTK/PyVistaなどは、時間変化する3D状態を生成する入力側の候補です。

## 目的

数理・科学Pythonは、幾何や運動の計算に強い。一方DCCは、カメラ、照明、文字、合成、編集、仕上げに強い。

このリポジトリは、**Pythonで運動を計算し、通常のアニメーション付き3DアセットとしてDCCへ受け渡す**ことに集中します。

## まず試す

現在の例はPython 3.13で確認しています。glTFとUSDの両方を出す場合は、

```powershell
uv python install 3.13
uv sync --extra usd
uv run python examples/02_lorenz_butterfly.py
```

を実行します。

生成されるファイルは、

```text
output/lorenz_butterfly.gltf
output/lorenz_butterfly.usda
```

です。

### After Effects

`lorenz_butterfly.gltf` を読み込み、

```text
Animation Options -> Name -> Lorenz_Butterfly_Flow
```

を選びます。

詳しくは [After Effects handoff](docs/after-effects.md) を参照してください。

### Resolve / Fusion

Fusionで `lorenz_butterfly.usda` を `uLoader` から読み込み、通常のUSDシーンとして `uRenderer` へ接続します。

詳しくは [Resolve / Fusion handoff](docs/resolve-fusion.md) を参照してください。

USDが不要なら、通常の `uv sync` だけでもglTF出力を使えます。

## Lorenzストレンジアトラクタ

看板デモではLorenz方程式をPythonで数値積分し、ほぼ同じ初期条件から始まる細い粒子束を動かします。

最初はほぼ重なっていますが、時間とともにストレンジアトラクタ上で分離します。60 fpsの密なモーションサンプル、全粒子で共有する滑らかな時間マップ、細いアトラクタ線、軽い残像表現を使っています。

```powershell
uv run python examples/02_lorenz_butterfly.py
```

重要なのは、**運動はPythonの数理モデルから来て、カメラ、照明、文字、合成、仕上げはDCC側に残る**ことです。

## 最小例

最小構成を確認するなら、

```powershell
uv run python examples/01_moving_cube.py
```

を実行します。USD supportを入れていれば、

```text
output/moving_cube.gltf
output/moving_cube.usda
```

の両方が生成されます。glTF内のアニメーション名は `MoveCube` です。

## 共通scene

内部表現は意図的に薄くしています。

```text
Scene
 └─ Node
     ├─ PyVista geometry
     ├─ display color / opacity
     ├─ hierarchy
     └─ TranslationTrack
```

ここから、

```text
Scene → glTF → After Effects
Scene → USD  → Resolve / Fusion
```

へ分岐します。

このscene modelをOpenUSDの代替に育てる意図はありません。将来camera、light、複雑なmaterial、reference、variant、deformationなどが必要になった場合は、OpenUSDそのものをcanonical representationにする選択肢を再検討します。

## なぜフレームごとに密にベイクするのか

初期のAfter Effects互換性テストでは、疎なglTFキーフレームは認識されたものの、キー境界で段差状に見えました。一方、出力先fpsごとに1サンプルを持たせると、テストしたAE環境では滑らかに再生されました。

そのためglTF backendでは、出力fpsを明示した密なサンプリングを基本にしています。これはglTF自体の制限ではなく、ホスト互換性のための方針です。

USD側も同じサンプリング済みscene stateをtime sampleとして書き出します。

## 現在確認できていること

- PyVistaの3D geometryをAfter Effectsへ実3Dモデルとして渡せる
- 複数nodeのtranslation animationを1つのglTFへ埋め込める
- 出力fpsで密にベイクしたmotionがAEで滑らかに再生する
- 同じ軽量sceneからUSDを出力できる
- Resolve/FusionでUSD geometryとtranslation animationを読み込み・再生できる

まだrotation/scale、camera/light、複雑なmaterial、deformation、instancingなどは扱っていません。

## 設計

```text
Python source of motion
        ↓
Scene / Node / TranslationTrack
        ↓
    ┌───────────────┐
    │               │
 glTF backend    USD backend
    │               │
After Effects   Resolve/Fusion
```

どちらも同じサンプリング済みscene stateから生成し、DCC側でカメラ、照明、合成、仕上げを行います。

詳細は [architecture notes](docs/architecture.md) を参照してください。

## License

MIT. See [LICENSE](LICENSE).
