<!--//Localized calendar dropdown

/*Starts the calendar dropdown
	Parameters:	CalID - the id of the href that is calling this function
							day - the day dropdown object to change
							month - the month dropdown object to change
	Dependencies:	step1scripts.xsl
								calendar.xsl
*/
var timeout = 500;
var timeoutId;
//write out the calendar div.
document.write('<div id="container"');
if (timeout) document.write(' onmouseout="calendarTimer();" onmouseover="if (timeoutId) clearTimeout(timeoutId);"');
document.write(' style="display: none;"></div>');

//create the date and calendar objects
var gED = new easyDate();	//from step1scripts.xsl
var gCal= new Calendar();

/*Closes the calendar after timeout (ms) has elapsed*/
function calendarTimer(){
	timeoutId=setTimeout('gCal.closeMe();',timeout);
}

/*Class Calendar encapsulates the dropdown calendar.*/
function Calendar(){
	this._iMonth	//currently selected month/year
	this._iDay		//Currently selected day
	this._endMonth;
	this._container=document.getElementById?document.getElementById('container'):document.all.container;
	this.objDay;				//reference to the day dropdown 
	this.objMonthYear;	//reference to the month dropdown
	this._currentMonth=0;	//default to first item in the list
	
	Calendar.prototype.showCalendar=function(calID, sDay, sMonthYear){
			
		//months in an array called shortMonthArray (Generated from calendar.xsl template ShortMonthlist)
		//days in an array called shortDayArray (Generated from calendar.xsl template ShortDayslist)
		try{
			this.objDay=(document.all)?document.all(sDay):document.getElementById(sDay);
			this.objMonthYear=(document.all)?document.all(sMonthYear):document.getElementById(sMonthYear);
			
			this._iDay=gED.getDay(this.objDay);
			this._iMonth=gED.getMonth(this.objMonthYear);

			if(this._iDay=='00'||this._iMonth=="00"){
				//day is set to No... set to todays date
				this._iDay=serverday;
				this._currentMonth=0;	//first item in the month dropdown list
				
			}else{
				//Current month is selected from the dropdown list
				this._currentMonth=this.getCurrentMonth(this.objMonthYear.options[this.objMonthYear.selectedIndex].value);	
			}
			//Build the calendar HTML
			var calendarHTML=this.buildCalendar(this._currentMonth);
			//Get the calendar button on the page
			var objCal=(document.all)?document.all(calID):document.getElementById(calID);
			//Set the calendar container properties
			this._container.innerHTML= calendarHTML;
			this._container.style.left=this.getElementX(objCal)+"px";
			this._container.style.top=parseInt(this.getElementY(objCal))+20+"px";
			this._container.style.zIndex=999;
			this._container.style.display="";
		
		}catch(e){
			//just hide me - no errors to user...
			this.closeMe();
		}
	}
	/* Main calendar class */
	Calendar.prototype.buildCalendar=function(iCurrentMonth) {

		//Get the current selected month
		var iMonth=this.getMonth(validMonthArray[iCurrentMonth]);
		var iYear=this.getYear(validMonthArray[iCurrentMonth]);
		//create a date object for the current selected month
		var currDate=new Date(iYear,iMonth-1,1);
		
		var month=currDate.getMonth()+1;
		var numDays=this.getDaysInMonth(month,iYear);
		var year=this.getFullYear(currDate);
				
		currDate.setDate(1); 
		
		var startDate=1;	//set to 0 for sunday, 1 for Monday, 2 for tuesday etc...
		
		var firstDay=(((currDate.getDay())+(7-startDate)) % 7);

		//build the html
		var calHTML='<table class="calTable" cellspacing="0" cellpadding="0"><tr><td height="20" width="15" class="calHeader">';
		//if not the first month, add a previous link
		if (iCurrentMonth>0){
			calHTML+='<a href="javascript:gCal.movePrevious()"><<</a>';
		}
		calHTML+='</td><td colspan="5" width="100" class="calHeader">'+ shortMonthArray[currDate.getMonth()+1] +' '+year+'</td><td class="calHeader" width="20">';
		//if not the last month, add a next link		
		if (iCurrentMonth<validMonthArray.length-1){
			calHTML+='<a href="javascript:gCal.moveNext()">>></a>';
		}
		calHTML+='</td></tr>'
		//Add the day titles
		for(var iDay=0;iDay<7;iDay++){
			calHTML+='<td height="20" width="20">'+shortDayArray[(iDay+startDate) % 7]+'</td>';
		}
		calHTML+='</tr>';
		//for each week in a possible 6 weeks to display...
		for(var iWeek=0;iWeek<6;iWeek++){
			calHTML+='<tr>';
			//for each day in a week
			for(iDay=1;iDay<8;iDay++){
				var dayWeekPos=(iWeek*7)+iDay;		//Get the actual position in the 7 day by 6 week matrix
				var dayOffset=dayWeekPos-firstDay;	//Get the offset from the day of the week
				
				var isValidDay=(dayWeekPos>firstDay)&&(dayOffset<=numDays);	//Is the day in the proper range?
				var beforeToday=(month==servermonth&&dayOffset<serverday);	//Is the day before todays date?
				var dateToShow=(isValidDay)?dayOffset:'';	//Only show days that are in this month
						
				//Write the day as a link if appropriate
				calHTML+='<td height="20">';
				calHTML+=(isValidDay&&!beforeToday)?'<a href="javascript:gCal.selectDay('+dateToShow+',\''+validMonthArray[iCurrentMonth]+'\')">':'';
				calHTML+=dateToShow;
				calHTML+=(isValidDay&&!beforeToday)?'</a>':'';
				calHTML+='</td>';
			}
			calHTML+='</tr>';
		}
		//write out the footer "close" link
		calHTML+='<tr><td height="20" class="calHeader">&nbsp;</td>'
		calHTML+='<td colspan="5" class="calHeader"><a href="javascript:gCal.closeMe()">'+sClose+'</a></td>'
		calHTML+='<td class="calHeader">&nbsp;</td></tr></table>'
				
		return calHTML;
	}
	/* gets the days in the month taking into account leap years */
	Calendar.prototype.getDaysInMonth=function(iMonth,iYear){
		if(iMonth==2){
			var febYear=(iMonth<=2)?iYear:iYear*1+1;
			var febDate=new Date(Date.UTC(febYear,1,29));
			return (febDate.getMonth()==1)?29:28;
		}
		else return (iMonth==4||iMonth==6||iMonth==9||iMonth==11)?30:31;
	}
	
	Calendar.prototype.getElementX=function(element){
		var x=element.offsetLeft;
		var oParent=element.offsetParent;
		while(oParent){
			x+=oParent.offsetLeft;
			oParent=oParent.offsetParent;}
		return x;
	}
	
	Calendar.prototype.getElementY=function(element){
		var y=element.offsetTop;
		var oParent=element.offsetParent;
		while(oParent){
			y+=oParent.offsetTop;
			oParent=oParent.offsetParent;}
		return y;
	}
	
	Calendar.prototype.closeMe=function(){
		this._container.style.left="";
		this._container.style.top="";
		this._container.style.display="none";
	}
	
	Calendar.prototype.movePrevious=function(){
		if(this._currentMonth>0){
			this._currentMonth--;
		}else{this._currentMonth=0;}
		var calendarHTML=this.buildCalendar(this._currentMonth);
		this._container.innerHTML= calendarHTML;
	}

	Calendar.prototype.moveNext=function(){
		if(this._currentMonth<validMonthArray.length-1){
			this._currentMonth++;
		}else{this._currentMonth=validMonthArray.length-1;}
		var calendarHTML=this.buildCalendar(this._currentMonth);
		this._container.innerHTML= calendarHTML;
	}
	
	Calendar.prototype.selectDay=function(iDay,iMonthYear){
		selectOption(this.objDay,iDay);
		selectOption(this.objMonthYear,iMonthYear);
		this.closeMe();
	}
	
	Calendar.prototype.getCurrentMonth=function(oMonthYear){
		for(var i=0;i<validMonthArray.length;i++){
			if(validMonthArray[i]==oMonthYear){return i;break;}
		}
	}
	
	Calendar.prototype.getMonth = function(sMonthYear){
		return sMonthYear.substring(0,2);
	}
		Calendar.prototype.getYear = function(sMonthYear){
		return sMonthYear.substring(2,6);
	}
	Calendar.prototype.getFullYear=function(date){
		fullyear = date.getYear();
		return (fullyear<1000)?fullyear+=1900:fullyear;
	} 
}

-->