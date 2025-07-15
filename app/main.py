import streamlit as st
import requests
import json
import pandas as pd

st.set_page_config(layout="wide")
st.title("疎通確認アプリ")

# バックエンド疎通確認セクション
st.subheader("1. バックエンド疎通確認")
user_query = st.text_area("テストクエリを入力してください:", height=100, key="backend_query")

if st.button("バックエンド疎通実行"):
    if user_query:
        st.info("バックエンドにリクエストを送信中...")
        
        try:
            response = requests.post("http://api:8000/analyze", json={"query": user_query})
            response.raise_for_status() # HTTP エラーがあれば例外を発生

            api_response = response.json()
            
            df = pd.DataFrame() # dfを初期化

            # データフレームの表示
            st.subheader("実行結果")
            try:
                df_json = api_response.get("data_json", "{}")
                df = pd.read_json(df_json, orient="split")
                # 日付カラムをdatetime型に変換し、表示形式を整形
                if 'date_order' in df.columns:
                    # 既にdatetime型でなければ変換
                    if not pd.api.types.is_datetime64_any_dtype(df['date_order']):
                        df['date_order'] = pd.to_datetime(df['date_order'], unit='ms') # unit='ms'を追加
                    # YYYY/MM/DD 形式の文字列カラムを追加（グラフ描画用）
                    df['date_formatted'] = df['date_order'].dt.strftime('%Y/%m/%d')

                st.write(f"デバッグ情報: df.empty after read_json = {df.empty}") # 追加
                st.write(f"デバッグ情報: df.head after read_json =\n{df.head()}") # 追加
                
                if not df.empty:
                    st.dataframe(df)
                    st.success("✅ SQLが実行され、データが取得されました！")
                else:
                    st.warning("⚠️ SQLは実行されましたが、データは返されませんでした。")

            except Exception as e:
                st.error(f"実行結果の表示中にエラーが発生しました: {e}")
                st.text(api_response.get("data_json")) # エラーの場合は生のJSONを表示

            # グラフの表示
            graph_metadata_str = api_response.get("graph_code")
            if graph_metadata_str:
                try:
                    graph_metadata = json.loads(graph_metadata_str)
                    graph_type = graph_metadata.get("type")
                    x_col = graph_metadata.get("x_col")
                    y_col = graph_metadata.get("y_col")
                    title = graph_metadata.get("title", "Generated Graph")
                    message = graph_metadata.get("message")

                    st.write(f"デバッグ情報: graph_metadata_str = {graph_metadata_str}")
                    st.write(f"デバッグ情報: graph_metadata = {graph_metadata}")
                    st.write(f"デバッグ情報: df.empty = {df.empty}")

                    if message:
                        st.warning(message)
                    elif graph_type and x_col and y_col and not df.empty:
                        st.subheader(title)
                        
                        # X軸が日付カラムの場合、整形済みカラムを使用
                        actual_x_col = x_col
                        if x_col == 'date_order' and 'date_formatted' in df.columns:
                            actual_x_col = 'date_formatted'

                        if graph_type == "line":
                            st.line_chart(df, x=actual_x_col, y=y_col)
                        elif graph_type == "bar":
                            st.bar_chart(df, x=actual_x_col, y=y_col)
                        elif graph_type == "scatter":
                            st.scatter_chart(df, x=actual_x_col, y=y_col)
                        else:
                            st.warning(f"サポートされていないグラフタイプです: {graph_type}")
                        st.success("✅ グラフが生成されました！")
                    else:
                        st.warning("⚠️ グラフを生成するための情報が不足しています。")
                except json.JSONDecodeError:
                    st.error("バックエンドから返されたグラフメタデータの形式が正しくありません。")
                    st.text(graph_metadata_str)
            else:
                st.warning("⚠️ グラフメタデータが返されませんでした。")

        except requests.exceptions.ConnectionError as e:
            st.error(f"❌ バックエンドへの接続に失敗しました。FastAPI サービスが起動しているか確認してください: {e}")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ HTTP エラーが発生しました: {e}")
        except json.JSONDecodeError:
            st.error("❌ バックエンドから無効なJSON応答を受け取りました。")
        except Exception as e:
            st.error(f"❌ 予期せぬエラーが発生しました: {e}")
