pyinstaller ^
	--clean ^
	--onefile ^
	--noconfirm ^
	--noconsole ^
	--add-data="RSLogger\img\pause.png;RSLogger\img" ^
	--add-data="RSLogger\img\rs_icon.ico;RSLogger\img" ^
	--add-data="RSLogger\img\questionmark_15.png;RSLogger\img" ^
	--add-data="RSLogger\img\record.png;RSLogger\img" ^
	--add-data="RSLogger\img\refresh_15.png;RSLogger\img" ^
	--name="RSLogger" ^
	--icon=RSLogger\img\rs_icon.ico ^
	main.py