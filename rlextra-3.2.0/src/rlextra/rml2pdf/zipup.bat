cd ..
del \tmp\rmlWin32standalone.zip
zip -u \tmp\rmlWin32standalone rml2pdf\*.bat rml2pdf\*.exe rml2pdf\rml_1_0.dtd rml2pdf\*.txt
zip -u \tmp\rmlWin32standalone rml2pdf\doc\*.rml rml2pdf\doc\images\*.gif
zip -u \tmp\rmlWin32standalone rml2pdf\demos\*.rml rml2pdf\demos\*.gif rml2pdf\mymodule.py
zip -u \tmp\rmlWin32standalone rml2pdf\test\*.rml
zip -d \tmp\rmlWin32standalone rml2pdf\zipup.bat
cd \tmp
rm -r -f rml2pdf
unzip rmlWin32standalone
cd rml2pdf
call runall.bat
cd \python\rlextra\rml2pdf
