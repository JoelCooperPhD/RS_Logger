pyinstaller ^
	--onefile ^
	--noconsole ^
	--clean ^
	--noconfirm ^
	--add-data="rs_icon.ico;." ^
	--add-data="RSLogger\img\questionmark_15.png;RSLogger\img" ^
	--add-data="RSLogger\img\record.png;RSLogger\img" ^
	--add-data="RSLogger\img\pause.png;RSLogger\img" ^
	--add-data="RSLogger\img\rs_icon.ico;RSLogger\img" ^
	--path="C:\Users\joelc\AppData\Local\Programs\Python\Python37-32\lib\site-packages\cv2" ^
	--add-data="C:\Users\joelc\AppData\Local\Programs\Python\Python37-32\lib\site-packages\cv2\opencv_videoio_ffmpeg454.dll;." ^
	--icon=rs_icon.ico ^
	--name="RS_Logger" ^
	main.py
