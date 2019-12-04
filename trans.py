import requests, json
import time,random,hashlib
from tkinter import *
from bs4 import BeautifulSoup
import pymysql
import re
from tkinter import ttk

class Translate(Frame):
    def __init__(self, master):
        self.master = master
        self.initWidgets()

    def initWidgets(self):
        self.text = Text(self.master,
                        width=44,
                        height=4,
                        font=('StSong', 14),
                        foreground='green')
        self.text.pack()
        self.text2 = Text(self.master,
                        width=44,
                        height=4,
                        font=('StSong', 14),
                        foreground='gray')
        self.text2.pack()
        f = Frame(self.master)
        f.pack()
        ttk.Button(f, text='翻译', command=self.cmd1).pack(side=LEFT)
        ttk.Button(f, text='详细翻译', command=self.detail_trans).pack(side=LEFT)
        ttk.Button(f, text='每日必会', command=self.query_sql).pack(side=LEFT)
    def cmd1(self):
        text_content = (self.text.get("0.0", "end").split("\n"))
        text_content.pop()  # 列表最后一个元素是空删除它
        print(text_content)
        self.dic_query(text_content)

    def dic_query(self,contents):
        self.text2.delete(10.0, 'end')  # 每次输出前先清空文本框
        try:
            for content in contents:
                url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule'#为避免{"errorCode":50}的错误，去除 url 中的_o
                ts = str(int(time.time() * 1000))
                salt = ts + str(random.randint(0,  9))
                bv = self.get_md5('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36')
                sign = self.get_md5("fanyideskweb" + content + salt + "n%A-rKaT5fb[Gy?;N5@Tj")
                key = {
                    'i': content,
                    'from': 'AUTO',
                    'to': 'AUTO',
                    'smartresult': 'dict',
                    'client': 'fanyideskweb',
                    'salt': salt,
                    'sign': sign,
                    'ts': ts,
                    'bv': bv,
                    'doctype': 'json',
                    'version': '2.1',
                    'keyfrom': 'fanyi.web',
                    'action': 'FY_BY_CLICKBUTTION'
                }
                rsp = requests.post(url=url, data=key).json()
                json.dumps(rsp, indent=2, sort_keys=True)
                a = rsp["translateResult"][0][0]["tgt"]  
                self.text2.insert('insert', a+'\n')
        except Exception as e:
            print("有道词典调用失败,{}".format(e))

    def get_md5(self,string):
        string  =  string.encode('utf-8')
        md5 = hashlib.md5(string).hexdigest()
        return md5

    def detail_trans(self):
        self.text2.delete(1.0, 'end')  # 每次输出前先清空文本框
        word = self.text.get(1.0, END)
        l = []
        try:
            r = requests.get(url='http://dict.youdao.com/w/eng/%s' % word)
            # "html.parser","lxml","html5lib"
            soup = BeautifulSoup(r.text, 'html.parser')
            s = soup.find(class_='trans-container')('ul')[0]('li')
            for item in s:
                if item.text:
                    l.append(item.text)
            l = "\n".join(l)
            self.text2.insert('insert',l)
        except Exception as e:
            print("Sorry, there is a error!\n",e)

    def get_url(self,base_url):
        for page in range(65):
            url = base_url + str(183+page)+'.html'
            content = self.get_word(url)
            self.parse(content)

    def get_word(self,url):
        try:
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
            rsp = requests.get(url=url, headers=headers)
            rsp.raise_for_status()
            rsp.encoding = 'utf-8'
            content = rsp.text
            return content
        except Exception as e:
            print('get word failed!{}'.format(e))

    def parse(self,content):
        soup = BeautifulSoup(content, 'html.parser')
        tags = soup.find(class_='artTxt')('p')
        try:
            for tag in tags:
                info=tag.get_text(strip=True).split(" ")[1:]
                re_info = self.check_data(info)
                if re_info is not None:
                    eng = info[0]
                    chinese = info[1]
                    self.db_sql(eng, chinese)
                elif info != '':
                    print('跳过{}'.format(info))
                    continue
                else:
                    pass
        except IndexError as e:
            print("IndexError:{}".format(str(e)))

    def check_data(self,info):
        re_info = re.search('\[.*\,.*\]',str(info))
        return re_info

    def db_sql(self,eng,chinese):
        try:
            connect = pymysql.Connect(
                        host='127.0.0.1',
                        port=3306,
                        user='root',
                        passwd='123456',
                        db='dictdata',
                        charset='utf8'
            )
            cursor = connect.cursor()
            sql = self.add_sql(eng,chinese)
            cursor.execute(sql)
            connect.commit()
        except Exception as e:
            print("DB execute failed.{}".format(e))
            connect.rollback()
        finally:
            if cursor is not None or cursor !="":
                cursor.close()
            if connect is not None or cursor !="":
                connect.close()

    def add_sql(self,eng,chinese):
        add = (eng, chinese)
        sql = "INSERT INTO t_dict (dic_word,dic_dest) VALUES(%s,%s)" % add
        return sql

    def query_sql(self):
        self.text2.delete(1.0, 'end')
        try:
            connect = pymysql.Connect(
                        host='127.0.0.1',
                        port=3306,
                        user='root',
                        passwd='123456',
                        db='dictdata',
                        charset='utf8'
            )
            cursor = connect.cursor()
            r_num = [random.randint(1, 5429) for i in range(3)]
            sql = "SELECT dic_word,dic_dest from t_dict where dic_id IN (%s,%s,%s)" % tuple(r_num)
            cursor.execute(sql)
            out_data = cursor.fetchall()
            out_data = [':'.join(od) for od in out_data]
            self.text2.insert('insert', out_data[0]+'\n'+out_data[1]+'\n'+out_data[2])

        except Exception as e:
            print("DB execute failed.{}".format(e))
            connect.rollback()
        finally:
            if cursor is not None or cursor != "":
                cursor.close()
            if connect is not None or cursor != "":
                connect.close()



        pass
if __name__ == "__main__":
    root = Tk()
    text_content = []
    root.title("Translate")
    Translate(root)
    root.mainloop()


