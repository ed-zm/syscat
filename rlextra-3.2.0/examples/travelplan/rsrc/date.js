var montharray=new Array("January","February","March","April","May","June","July","August","September","October","November","December");

function searchValidate(){
			var f =  document.forms['searchForm'];
			var oDate = new Date();
			var rDate = new Date();
			var orig = f.orig.value;
			var dest = f.dest.value;
			oDay = f.oDay.value;
			oMonYear = f.oMonYear.value;
			oMon = oMonYear.substring(0,2)-1;
			oYear = oMonYear.substring(2,6);
			rDay = f.rDay.value;
			rMonYear = f.rMonYear.value;
			rMon = rMonYear.substring(0,2)-1;
			rYear = rMonYear.substring(2,6);
			oDate.setFullYear(oYear, oMon, oDay);
			rDate.setFullYear(rYear, rMon, rDay);
			tripTitle = f.tripTitle.value;
			subtitle = f.subtitle.value;
			var msg = "";
			if (orig == "") msg= msg+"Departure city/airport is not specified.";
			if (dest == "") msg = msg+"\nDestination city/airport is not specified.";
			if(rMonYear!='000000' && rDate<oDate) msg = msg+'\nReturn date must not be earlier than departure date!';
			if(msg!="") {
				alert(msg)
				return false;
				}
			else{
				if (tripTitle=='') f.tripTitle.value = ' ';
				if (subtitle=='') f.subtitle.value = ' ';
				return true;
				}
			}

function getNumOfDays(MonYear){
	m = MonYear.substring(0,2);
	y = MonYear.substring(2,6);
	if ((m==4)||(m==6)||(m==9)||(m==11)) days = 30;
	else if(m==2){
		if (y%4==0 && y%100!=0 || y%400==0) days = 29;
		else days = 28;
		}
	else days = 31;
	return days;
}

function setDayOptions(id,lYMD,token){
	ldateArray=lYMD.split('-');
	lmonYear=to2Digits(parseInt(ldateArray[1],10)).toString()+ldateArray[0]
	lday=parseInt(ldateArray[2],10)
	dropdown=document.getElementById(id);
	dropdown.options.length=0;
	numOfDays = getNumOfDays(lmonYear)
	with(dropdown){
		for (i = lday; i <= numOfDays; i++){
			s = to2Digits(i);
			options[i-lday] = new Option(s, s);
			} 
		if (token=='u')	options.selectedIndex=numOfDays-lday;
		else options.selectedIndex=0;
	}
}

function setDayOptions2(id,uYMD,token){
	udateArray=uYMD.split('-');
	umonYear=to2Digits(parseInt(udateArray[1],10)).toString()+udateArray[0]
	uday=parseInt(udateArray[2],10)
	dropdown=document.getElementById(id);
	dropdown.options.length=0;
	numOfDays = getNumOfDays(umonYear)
	with(dropdown){
		for (i = 1; i <= uday; i++){
			s = to2Digits(i);
			options[i-1] = new Option(s, s);
			} 
		if (token=='u')	options.selectedIndex=uday-1;
		else options.selectedIndex=0;
	}
}

function genDayOptions(MonYear, id, lYMD, uYMD, token){
	ldateArray=lYMD.split('-');
	lMY=to2Digits(parseInt(ldateArray[1],10)).toString()+ldateArray[0];
	udateArray=uYMD.split('-');
	uMY=to2Digits(parseInt(udateArray[1],10)).toString()+udateArray[0];
	days = getNumOfDays(MonYear);
	dropdown=document.getElementById(id);
	dropdown.options.length=0;
	with(dropdown){
	if(MonYear=='000000'){
		options[0] = new Option('no','00');
		options.selectedIndex=0;
		}
	else if(MonYear==lMY) setDayOptions(id,lYMD,token);
	else if(MonYear==uMY) setDayOptions2(id,uYMD,token);
	else{
		for (i = 1; i <= days; i++) {
			s = to2Digits(i);
			options[i-1] = new Option(s,s);
			}
  		}
	}
}

function genMonYearOptions(id,lYMD,uYMD,token){
		var lDate = new Date();
		var uDate = new Date();
		ldateArray = lYMD.split('-');
		udateArray = uYMD.split('-');
		lDate.setFullYear(parseInt(ldateArray[0],10),parseInt(ldateArray[1],10)-1,parseInt(ldateArray[2],10));
		if (uYMD=='0000-00-00') uDate.setFullYear(parseInt(ldateArray[0],10),parseInt(ldateArray[1],10)+11,parseInt(ldateArray[2],10));
		else uDate.setFullYear(parseInt(udateArray[0],10),parseInt(udateArray[1],10)-1,parseInt(udateArray[2],10));
		dropdown=document.getElementById(id);
		var l=dropdown.options.length;
		with(dropdown){
				var i=0;
				for(iDate=new Date(lDate.valueOf()); (iDate.getYear()<uDate.getYear())||((iDate.getYear()==uDate.getYear())&&(iDate.getMonth()<=uDate.getMonth())); iDate.setMonth(newMonth+(++i))){
						year = (iDate.getYear() < 1000) ? 1900 + iDate.getYear():iDate.getYear();
						v = to2Digits(iDate.getMonth()+1)+year.toString();
						s = montharray[iDate.getMonth()]+' '+year.toString();
						options[l+i] = new Option(s, v);
						iDate = new Date(lDate.valueOf());		
						newMonth=lDate.getMonth();
						iDate.setDate(1);
				}
				if (token=='u') options.selectedIndex=l+i-1 
				else options.selectedIndex=0 
		}
}


function to2Digits(num){
	var n;
	if (num>=0 && num<10){
		n = '0'+num.toString();
		}
	else if(num>=10 && num<100){
		n = num.toString();
		}
	return n;
	}

function DMY2YMD(DMY){
	dateArray=DMY.split('-');
	return dateArray[2]+'-'+dateArray[1]+'-'+dateArray[0];
}

function YMD2DMY(YMD){
	dateArray=YMD.split('-');
	return dateArray[2]+'-'+dateArray[1]+'-'+dateArray[0];
}

function getDateObj(YMD){
	Y=parseInt(YMD.substring(0,4),10)
	M=parseInt(YMD.substring(5,7),10)-1
	D=parseInt(YMD.substring(8,10),10)
	dateObj=new Date()
	dateObj.setFullYear(Y,M,D)
	return dateObj	
}
