import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse

# [핵심 변경] 구글 뉴스 RSS 피드를 안전하게 파싱하는 함수
def get_climate_news(keyword):
    # 한글 검색어가 깨지지 않도록 인코딩
    encoded_keyword = urllib.parse.quote(keyword)
    
    # 구글 뉴스 RSS 검색 URL (hl=ko: 한국어, gl=KR: 대한민국 국가설정)
    url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # RSS는 XML 형식이므로 xml 파서나 html 파서로 읽을 수 있습니다.
            soup = BeautifulSoup(response.text, 'lxml-xml')
            
            # RSS 피드 안에서 각 기사는 <item> 태그 안에 담겨 있습니다.
            items = soup.find_all('item')
            
            if not items:
                return None
                
            news_list = []
            for item in items:
                title = item.title.get_text()
                link = item.link.get_text()
                
                # 구글 뉴스 RSS 제목 특성상 끝에 ' - 언론사명'이 붙으므로 정돈 원할 시 처리 가능
                # 여기서는 원본 제목 그대로 가져옵니다.
                news_list.append({"기사 제목": title, "링크": link})
            
            return news_list
        else:
            messagebox.showerror("오류", f"구글 RSS 서버 응답 실패 (상태코드: {response.status_code})")
            return None
    except Exception as e:
        messagebox.showerror("시스템 오류", f"RSS 파싱 중 에러 발생:\n{str(e)}")
        return None

# --- UI 및 버튼 이벤트 소스 ---
def start_crawl():
    keyword = entry.get().strip()
    if not keyword:
        messagebox.showwarning("경고", "검색어를 입력해 주세요!")
        return
        
    for item in tree.get_children():
        tree.delete(item)
        
    status_label.config(text="구글 RSS 피드에서 안전하게 뉴스 수집 중...", fg="blue")
    root.update()
    
    global crawled_data
    crawled_data = get_climate_news(keyword)
    
    if crawled_data:
        for idx, news in enumerate(crawled_data, 1):
            tree.insert("", "end", values=(idx, news["기사 제목"], news["링크"]))
        status_label.config(text=f"총 {len(crawled_data)}개의 뉴스를 가져왔습니다.", fg="green")
        btn_save.config(state="normal")
    else:
        status_label.config(text="뉴스 수집 실패", fg="red")
        messagebox.showinfo("안내", f"'{keyword}' 관련 뉴스 피드를 찾을 수 없습니다.")

def save_to_excel():
    if not crawled_data: return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        initialfile=f"{entry.get()}_뉴스_리스트.csv"
    )
    if file_path:
        df = pd.DataFrame(crawled_data)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        messagebox.showinfo("완료", "파일이 성공적으로 저장되었습니다!")

# UI 구성
root = tk.Tk()
root.title("🌱 기후 뉴스 실시간 수집기 (RSS 우회형)")
root.geometry("700x500")
crawled_data = []

frame_top = tk.Frame(root, padx=10, pady=10)
frame_top.pack(fill="x")
lbl = tk.Label(frame_top, text="검색어 입력:", font=("맑은 고딕", 10))
lbl.pack(side="left", padx=5)
entry = tk.Entry(frame_top, width=30, font=("맑은 고딕", 10))
entry.insert(0, "기후변화")
entry.pack(side="left", padx=5)
btn_search = tk.Button(frame_top, text="뉴스 수집", command=start_crawl, bg="#2ecc71", fg="white", font=("맑은 고딕", 10, "bold"))
btn_search.pack(side="left", padx=5)
btn_save = tk.Button(frame_top, text="엑셀 저장", command=save_to_excel, state="disabled", bg="#3498db", fg="white", font=("맑은 고딕", 10, "bold"))
btn_save.pack(side="left", padx=5)

status_label = tk.Label(root, text="검색어를 입력하고 뉴스 수집을 눌러주세요.", font=("맑은 고딕", 9), anchor="w", padx=15)
status_label.pack(fill="x")

frame_mid = tk.Frame(root, padx=10, pady=5)
frame_mid.pack(fill="both", expand=True)
columns = ("번역", "제목", "링크")
tree = ttk.Treeview(frame_mid, columns=columns, show="headings")
tree.heading("번역", text="번호")
tree.heading("제목", text="기사 제목")
tree.heading("링크", text="링크")
tree.column("번역", width=50, anchor="center")
tree.column("제목", width=350)
tree.column("링크", width=250)
scrollbar = ttk.Scrollbar(frame_mid, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
tree.pack(side="left", fill="both", expand=True)

root.mainloop()