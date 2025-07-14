import streamlit as st
import requests
import json

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
            
            st.subheader("バックエンドからの応答")
            # data_jsonはJSON文字列なので、再度パースする
            try:
                sql_data = json.loads(api_response.get("data_json", "{}"))
                sql_query = sql_data.get("sql", "SQLクエリが見つかりませんでした。")
                
                st.write("生成されたSQLクエリ:")
                st.code(sql_query, language="sql")
                st.success("✅ バックエンド疎通確認成功！")

            except json.JSONDecodeError:
                st.error("バックエンドから返されたdata_jsonの形式が正しくありません。")
                st.json(api_response) # エラーの場合は生の応答を表示

        except requests.exceptions.ConnectionError as e:
            st.error(f"❌ バックエンドへの接続に失敗しました。FastAPI サービスが起動しているか確認してください: {e}")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ HTTP エラーが発生しました: {e}")
        except json.JSONDecodeError:
            st.error("❌ バックエンドから無効なJSON応答を受け取りました。")
        except Exception as e:
            st.error(f"❌ 予期せぬエラーが発生しました: {e}")
    else:
        st.warning("テストクエリを入力してください。")

st.markdown("--- ")

# LLM 疎通確認セクション
st.subheader("2. LLM 疎通確認")
if st.button("LLM 疎通実行"):
    st.info("LLM にリクエストを送信中...")
    try:
        # LLM テストエンドポイントを叩く
        response = requests.get("http://api:8000/test_llm")
        response.raise_for_status() # HTTP エラーがあれば例外を発生

        llm_test_response = response.json()
        
        st.subheader("LLM からの応答")
        st.json(llm_test_response)

        if llm_test_response.get("llm_response"):
            st.success(f"✅ LLM 疎通確認成功！応答: {llm_test_response.get('llm_response')}")
        else:
            st.warning("⚠️ LLM からの応答が空でした。")

    except requests.exceptions.ConnectionError as e:
        st.error(f"❌ バックエンドへの接続に失敗しました。FastAPI サービスが起動しているか確認してください: {e}")
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP エラーが発生しました: {e}")
    except json.JSONDecodeError:
        st.error("❌ バックエンドから無効なJSON応答を受け取りました。")
    except Exception as e:
        st.error(f"❌ 予期せぬエラーが発生しました: {e}")
st.markdown("--- ")

# LangGraph 疎通確認セクション
st.subheader("3. LangGraph 疎通確認")
if st.button("LangGraph 疎通実行"):
    st.info("LangGraph にリクエストを送信中...")
    try:
        # LangGraph テストエンドポイントを叩く
        response = requests.get("http://api:8000/graph_test")
        response.raise_for_status() # HTTP エラーがあれば例外を発生

        graph_test_response = response.json()
        
        st.subheader("LangGraph からの応答")
        st.json(graph_test_response)

        if graph_test_response.get("user_query") == "foo":
            st.success(f"✅ LangGraph 疎通確認成功！")
        else:
            st.warning("⚠️ LangGraph からの応答が期待したものではありませんでした。")

    except requests.exceptions.ConnectionError as e:
        st.error(f"❌ バックエンドへの接続に失敗しました。FastAPI サービスが起動しているか確認してください: {e}")
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP エラーが発生しました: {e}")
    except json.JSONDecodeError:
        st.error("❌ バックエンドから無効なJSON応答を受け取りました。")
    except Exception as e:
        st.error(f"❌ 予期せぬエラーが発生しました: {e}")
