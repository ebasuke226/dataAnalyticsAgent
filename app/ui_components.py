import streamlit as st
import pandas as pd
import json
import api_client

def backend_communication_section():
    st.subheader("1. データ自動分析")
    user_query = st.text_area("テストクエリを入力してください:", height=100, key="backend_query")

    if st.button("分析実行実行"):
        if user_query:
            st.info("バックエンドにリクエストを送信中...")
            try:
                response = api_client.analyze_query(user_query)
                response.raise_for_status()
                api_response = response.json()

                df = pd.DataFrame()

                st.subheader("実行結果")
                try:
                    df_json = api_response.get("data_json", "{}")
                    df = pd.read_json(df_json, orient="split")
                    if 'date_order' in df.columns:
                        df['date_order'] = pd.to_datetime(df['date_order'], unit='ms').dt.strftime('%Y/%m/%d')
                    if not df.empty:
                        st.dataframe(df)
                    else:
                        st.warning("⚠️ SQLは実行されましたが、データは返されませんでした。")
                except Exception as e:
                    st.error(f"実行結果の表示中にエラーが発生しました: {e}")
                    st.text(api_response.get("data_json"))

                graph_metadata_str = api_response.get("graph_code")
                if graph_metadata_str:
                    try:
                        graph_metadata = json.loads(graph_metadata_str)
                        graph_type = graph_metadata.get("type")
                        x_col = graph_metadata.get("x_col")
                        y_col = graph_metadata.get("y_col")
                        title = graph_metadata.get("title", "Generated Graph")
                        message = graph_metadata.get("message")

                        if message:
                            st.warning(message)
                        elif graph_type and x_col and y_col and not df.empty:
                            st.subheader(title)
                            if graph_type == "line":
                                st.line_chart(df, x=x_col, y=y_col)
                            elif graph_type == "bar":
                                st.bar_chart(df, x=x_col, y=y_col)
                            elif graph_type == "scatter":
                                st.scatter_chart(df, x=x_col, y=y_col)
                            else:
                                st.warning(f"サポートされていないグラフタイプです: {graph_type}")
                        else:
                            st.warning("⚠️ グラフを生成するための情報が不足しています。")
                    except json.JSONDecodeError:
                        st.error("バックエンドから返されたグラフメタデータの形式が正しくありません。")
                        st.text(graph_metadata_str)
                else:
                    st.warning("⚠️ グラフメタデータが返されませんでした。")

                insights_text = api_response.get("insights")
                if insights_text:
                    st.subheader("分析インサイト")
                    st.write(insights_text)
                else:
                    st.warning("⚠️ 分析インサイトが返されませんでした。")

            except requests.exceptions.RequestException as e:
                st.error(f"❌ バックエンドへの接続に失敗しました: {e}")
            except Exception as e:
                st.error(f"❌ 予期せぬエラーが発生しました: {e}")
        else:
            st.warning("テストクエリを入力してください。")

