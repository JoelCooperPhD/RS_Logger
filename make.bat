pyinstaller ^
	--onefile ^
	--noconsole ^
	--clean ^
	--noconfirm ^
	--add-data="rs_icon.ico;." ^
	--add-data="RSLogger\img\questionmark_15.png;RSLogger\img" ^
	--add-data="RSLogger\img\record.png;RSLogger\img" ^
	--add-data="RSLogger\img\pause.png;RSLogger\img" ^
	--icon=rs_icon.ico ^
	--name="RS_Logger" ^
	main.py
