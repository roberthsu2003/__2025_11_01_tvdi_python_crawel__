import os
def get_html_path()-> str:
    """返回HTML文件的絕對路徑"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "waiting_demo.html")
    return f"file://{html_path}"

def main():
    path = get_html_path()
    print(path)

if __name__ == "__main__":
    main()