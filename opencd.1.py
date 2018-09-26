# coding=utf-8
import os
import re
import pickle
import requests
import requests.utils
from PIL import Image
import captchaparse as cp
import time
import logging
#imgpath = 'check_code.jpg'

logging.basicConfig(filename='logger.log', level=logging.INFO)

ascii_char = list(r"$@&%B#... ")
def select_ascii_char(r, g, b):
	gray = int((19595 * r + 38469 * g + 7472 * b) >> 16)  # ‘RGB－灰度值’转换公式
	unit = 256.0 / len(ascii_char)  # ascii_char中的一个字符所能表示的灰度值区间
	return ascii_char[int(gray / unit)]
# 返回给定路径图片的字符表示，用户在此还可以指定输出字符画的宽度和高度
def output(imgpath, width=150, height=100):
	im = Image.open(imgpath)
	im = im.resize((width, height), Image.NEAREST)
	# 裁剪
	box = (0, 30, width, 70)
	# 这里的参数可以这么认为：从某图的(x,y)坐标开始截，截到(width+x,height+y)坐标
	# 所包围的图像，crop方法与php中的imagecopy方法大为不一样
	newIm = im.crop(box)
	txt = ""
	for h in range(newIm.size[1]):
		for w in range(newIm.size[0]):
			txt += select_ascii_char(*newIm.getpixel((w, h))[:3])  # 此处请看详解（1）
		txt += '\n'
	return txt
def save_as_txtfile(txt,imgpath):
	with open(imgpath.split('.')[0]+'.txt', 'w') as f:
		f.write(txt)
def codeBegin(imgpath):
	print(output(imgpath))
	save_as_txtfile(output(imgpath), imgpath)
	
def getCheckCode(imageHash):

	image_get_url = 'https://open.cd/image.php?action=regimage&imagehash=' + imageHash
	imgpath = imageHash + '.jpg'
	abs_imgpath = os.path.join(os.path.abspath('.'), imgpath)
	im = requests.get(image_get_url)  # 获取验证码和cookies值
	with open(abs_imgpath, 'wb') as f:
		f.write(im.content)
	# img = Image.open('check_code.jpg')
	# img.show()
	'''
	codeBegin(imgpath)
	check_code = input("code:")
	'''
	check_code = cp.binary_captchar(abs_imgpath)

	os.remove(abs_imgpath)
	#print("captcha: " + check_code)
	return check_code

def login():
	'''
	获取登陆会话
	'''
	files = os.listdir('.')
	cookie_file_name='open_cookies.txt'
	if cookie_file_name in files:
		with open(cookie_file_name, 'rb') as f:
			cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
			bt_session = requests.session()
			bt_session.cookies = cookies
		try:
			torrent_url = 'https://open.cd/torrents.php'
			test = bt_session.get(torrent_url)
			if test.status_code != 200 or test.url != torrent_url:
				print('Something wrong when login in. Delete the cookies and relogin plese.\n')
				return
		except:
			print("net error")
			return
	else:
		username = input("your username:")
		password = input("your password:")
		login_php = 'https://open.cd/login.php'
		try:
			bt_session = requests.Session()
			req = bt_session.get(login_php)
		except:
			print("net error")
			return
		#print(req.text)
		# <input name="imagehash" value="2cb98173c9a2fc28f0976f9a5b715db5">
		imageHash = re.findall('name="imagehash" value="(.*?)" />', req.text)[0]
		print(imageHash)
		#image_get_url = 'https://open.cd/image.php?action=regimage&imagehash=' + imageHash
		check_code = getCheckCode(imageHash)
		login_post_url = 'https://open.cd/takelogin.php'
		login_datas = {
			'username': username,
			'password': password,
			'imagestring': check_code,
			'imagehash': imageHash
		}
		try:
			main_page = bt_session.post(login_post_url, login_datas)
			print(main_page.text)
			if main_page.url != "https://open.cd/index.php":
				print("login error")
				return
			with open(cookie_file_name, 'wb') as f:
				pickle.dump(requests.utils.dict_from_cookiejar(bt_session.cookies), f)
			print('成功登陆')
		except:
			print("net error")
	return bt_session

def checkin(session):
	'''
	签到
	'''
	checkin_php = 'https://open.cd/plugin_sign-in.php'
	try:
		req = session.get(checkin_php)
	except:
		print('check in error')
		return
	imageHash = re.findall('name="imagehash" value="(.*?)"/>', req.text)[0]
	#print(imageHash)
	#image_get_url = 'https://open.cd/image.php?action=regimage&imagehash=' + imageHash
	
	#print(getCheckCode(imageHash))
	check_code = getCheckCode(imageHash)
	checkin_post_url= 'https://open.cd/plugin_sign-in.php?cmd=signin'

	checkin_datas = {
		'imagehash': imageHash,
		'imagestring' : check_code
	}
	try:
		checkin_page = session.post(checkin_post_url, checkin_datas)
		print(checkin_page.json())
		
		if(checkin_page.json()['state'] == 'false' and checkin_page.json().has_key('msg')):
			checkin(session)
		elif(checkin_page.json()['state'] == 'success'):
			nowtime = time.strftime('%Y-%m-%d', time.localtime(time.time()))
			str = nowtime + '\t签到成功\t连续签到：' + checkin_page.json()['signindays'] + '天,\t获得魔力值：' + checkin_page.json()['integral']
			print(str)
			logging.info(str)
		elif(checkin_page.json()['state'] == 'false' and not checkin_page.json().has_key('msg')):
			print('已经签到')
			

	except:
		print("net error")

if __name__ == '__main__':
	session = login()
	checkin(session)



