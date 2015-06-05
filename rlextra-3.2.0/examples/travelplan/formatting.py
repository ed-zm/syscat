"""
Put here all formatting require for the travel plan application

"""

import datetime

def formatDate(stringDate):
    """ Takes a string date as '2006-04-26' and turns it into a formatted date as 'Tuesday, 04 Jul 2006'."""
    date = stringDate.split('-')
    intDate = list(map(int, date))
    day = intDate[2]
    month = intDate[1]
    year = intDate[0]
    fmtDate = datetime.date(year, month,day)
    return fmtDate.strftime("%a, %d %b %Y")

def getTripLength(strDateArrive, strDateDepart):
    darrv = strDateArrive.split('-')
    ddep = strDateDepart.split('-')
    intdarrv = list(map(int, darrv))
    intddep = list(map(int, ddep))
    dateArrive = datetime.date(intdarrv[0], intdarrv[1], intdarrv[2])
    dateDepart = datetime.date(intddep[0], intddep[1], intddep[2])
    days_diff = dateArrive - dateDepart
    return days_diff
