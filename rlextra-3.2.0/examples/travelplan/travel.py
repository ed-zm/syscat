 #travel plan application
from datetime import date, timedelta
_flightClass = {'first':['A','F','G','P'],
               'business':['C','D','I','J','Z'],
               'economy':['B','E','H','K','L','M','N','O','Q','R','S','T','U','V','W','X','Y']
    }
class ItemMapping(dict):
    def __setattr__(self, name, value):
        self[name] = value
    def __getattr__(self, name):
        return self[name]


class City(ItemMapping):
    def toXML(self):
        cityName='<name>'+self.displayName+'</name>'
        intro='<intro>'+self.intro+'</intro>'
        description='<description>'+self.description+'</description>'
        weatherInfo='<weatherInfo>'+self.weatherInfo+'</weatherInfo>'
        img='<img>'+'city_'+self.id+'.jpg</img>'
        xml='\n\t'.join(['<city>',cityName,intro,description,weatherInfo,img])+'\n</city>'
        return xml

class Airport(ItemMapping):
    def __str__(self):
        airportInfo='Name: %s,  Code: %s, City: %s' %(self.id, self.displayName, cities[self.city_id][displayName])
        return airportInfo

class Airline(ItemMapping): pass

class Flight(ItemMapping):
    def __str__(self):
        departureCity = cities[airports[self.departureAirport]['city_id']]['displayName']
        arrivalCity = cities[airports[self.arrivalAirport]['city_id']]['displayName']
        airline = self.id.split('_')[0].lower()
        airlineLogo = airline+'.gif'
        line1 = self.id.replace('_', '') + airlineLogo
        line2 = '%s (%s Terminal %s) ---> %s (%s Terminal %s)    %s km' %(departureCity, self.departureAirport, self.departureTerminal, arrivalCity, self.arrivalAirport, self.arrivalTerminal, self.distance)
        if not self.isOverNight: line3 = 'Depart %s                Arrive %s  Duration %s' %(self.departureTime, self.arrivalTime, self.duration)
        else: line3 = 'Depart %s                Arrive %s +1 day  Duration Duration %s' %(self.departureTime, self.arrivalTime, self.duration)
        flightInfo = '\n'.join([line1,line2,line3])
        return flightInfo
    def toXML(self, flightClass=None, departureDate=None):
        if departureDate is None:
            departureDate = 'Not Specified'
        dd = '<date>'+departureDate+'</date>'
        fare = ticketfares[self.id]
        distance = '<distance>'+str(self.distance)+'</distance>'
        duration = '<duration>'+str(self.duration)+'</duration>'
        isOverNight = '<isOverNight>'+str(self.isOverNight)+'</isOverNight>'
        airlineLogo = '<airlineLogo>'+self.id.split('_')[0].lower()+'.gif'+'</airlineLogo>'
        departureCity = '<city>'+cities[airports[self.departureAirport]['city_id']]['displayName']+'</city>'
        departureAirport = '<airport>'+self.departureAirport+'</airport>'
        departureTerminal = '<terminal>'+self.departureTerminal+'</terminal>'
        departureTime = '<time>'+self.departureTime+'</time>'
        depart = '<depart>'+'\n\t\t'+'\n\t\t'.join([departureCity,departureAirport,departureTerminal,departureTime])+'\n\t'+'</depart>'
        arrivalCity = '<city>'+cities[airports[self.arrivalAirport]['city_id']]['displayName']+'</city>'
        arrivalAirport = '<airport>'+self.arrivalAirport+'</airport>'
        arrivalTerminal = '<terminal>'+self.arrivalTerminal+'</terminal>'
        if self.isOverNight:
            arrivalTime = '<time>'+self.arrivalTime+'+1day </time>'
        else:
            arrivalTime = '<time>'+self.arrivalTime+'</time>'
        arrive = '<arrive>'+'\n\t\t'+'\n\t\t'.join([arrivalCity,arrivalAirport,arrivalTerminal,arrivalTime])+'\n\t'+'</arrive>'
        xml = '<flight id="'+self.id+'">'+'\n\t'+'\n\t'.join([dd, distance, duration, isOverNight, airlineLogo, depart, arrive])+'\n'+'</flight>'
        return xml

class FlightFare(ItemMapping): pass

class Hotel(ItemMapping):
    def toXML(self, room_id=None):
        city='<city>'+self.city+'</city>'
        displayName='<displayName>'+self.displayName+'</displayName>'
        starRating='<starRating>'+self.starRating+'</starRating>'
        address='<address>'+self.address+'</address>'
        telephone='<telephone>'+self.telephone+'</telephone>'
        img='<image>'+self.img+'</image>'
        description='<description>'+self.description+'</description>'
        roomDesc='<roomDesc>'+self.roomDesc+'</roomDesc>'
        roomImg='<roomImg>'+self.roomImg+'</roomImg>'
        roomList=[]
        for (id, room) in list(rooms.items()):
            if room_id in [None, room['id']] and room['hotel']==self.id:
                roomList.append(room.toXML().replace('\n','\n\t'))
        roomXML='\n\t'.join(roomList)
        xml='\n\t'.join(['<hotel id="%s">' %self.id,city,displayName,starRating,address,telephone,img,description,roomDesc,roomImg,roomXML])+'\n</hotel>'
        return xml

class Room(ItemMapping):
    def toXML(self):
        type = '<type>'+self.type+'</type>'
        capacity = '<capacity>'+str(self.capacity)+'</capacity>'
        hasBreakfast = '<hasBreakfast>'+str(self.hasBreakfast)+'</hasBreakfast>'
        price = '<price>'+str(self.price)+'</price>'
        xml = '\n\t'.join(['<room id="%s">' %self.id,type,hasBreakfast,price])+'\n</room>'
        return xml

def getCities():
    return {
            'london':
                City(id='london', displayName='London', country_id='GB'),

            'paris':
                City(id='paris', displayName='Paris', country_id='FR',
                     intro="Paris, the capital of France, is the spiritual home of all things chic and artistic. From the central grand boulevards to the out-of-the-way charm of Montmartre, the city's 28 million visitors a year are rarely disappointed with their visit.",
                     description="If aliens chanced upon Paris, they would have good reason to believe they had discovered the capital of the world. It is hard to think of a city that has such a vast array of impressive buildings, monuments and gardens. From the infamous (Eiffel Tower, Arc de Triumph, Notre Dame) to the well-loved (Sacre Coeur, Jardin du Luxembourg, Musee d'Orsay) and the must-see (Louvre, Pompidou and Champs Elysees) - Paris has it all.",
                     weatherInfo="The average January temperature in Paris is a chilly 3 degrees Celsius (37 degrees Fahrenheit) rising steadily to a fairly warm spring and very pleasant July average of approximately 26 degrees Celsius (79 degrees Fahrenheit). Rain falls consistently throughout the year with only the occasional Northern European heat wave causing prolonged dry periods."),

            'phuket':
                City(id='phuket', displayName='Phuket', country_id='TH',
                     intro="Known as the 'Pearl of the Andaman Sea', Phuket is a beautiful palm-fringed island offering pristine sandy beaches, clear blue seas, colourful night markets, soaring mountains and forests of tall coconut palms.",
                     description="It's a very prosperous place, blessed with long stretches of white sand beach hidden in sheltered coves. At the end of a lazy day, nature creates its own magical event with stunning sunsets setting the sky on fire. Water sports facilities are excellent at the hotels, and a boat trip past amazing Phang Nga Bay, with its stunning limestone scenery, is essential.",
                     weatherInfo="It is warm in Phuket all year round with temperatures ranging between 25 - 34°C (77 - 93°F). Phuket's weather is typically divided into two distinct seasons, dry and rainy, with transitional periods in between. The seasons are dictated by the tropical monsoon."),

            'bangkok':
                City(id='bangkok', displayName='Bangkok', country_id='TH'),

            'frankfurt':
                City(id='frankfurt', displayName='Frankfurt', country_id='DE'),

            'singapore':
                City(id='singapore', displayName='Singapore', country_id='SG'),
            }

def getFlights():
    return {
            'AF_2671':Flight(id='AF_2671', departureAirport='LHR', departureTerminal='2', arrivalAirport='CDG', arrivalTerminal='2F', departureTime='08:45', isOverNight=False, arrivalTime='11:00', distance=354, duration='1hr 15min'),
            'AF_1570':Flight(id='AF_1570', departureAirport='CDG', departureTerminal='2F', arrivalAirport='LHR', arrivalTerminal='2', departureTime='12:00', isOverNight=False, arrivalTime='12:15', distance=354, duration='1hr 15min'),
            'AF_5021':Flight(id='AF_5021', departureAirport='LCY', departureTerminal='2', arrivalAirport='CDG', arrivalTerminal='2F', departureTime='09:05', isOverNight=False, arrivalTime='11:15', distance=354, duration='1hr 10min'),
            'AF_5026':Flight(id='AF_5026', departureAirport='CDG', departureTerminal='2F', arrivalAirport='LCY', arrivalTerminal='', departureTime='17:55', isOverNight=False, arrivalTime='18:00', distance=354, duration='1hr 10min'),
            'TG_917':Flight(id='TG_917', departureAirport='LHR', departureTerminal='', arrivalAirport='BKK', arrivalTerminal='', departureTime='21:30', isOverNight=True, arrivalTime='15:05',distance=0, duration='10hr 35min'),
            'TG_217':Flight(id='TG_217', departureAirport='BKK', departureTerminal='', arrivalAirport='HKT', arrivalTerminal='', departureTime='16:45', isOverNight=False, arrivalTime='18:05',distance=0, duration='1hr 20min'),
            'LH_4727':Flight(id='LH_4727', departureAirport='LHR', departureTerminal='', arrivalAirport='FRA', arrivalTerminal='', departureTime='11:50', isOverNight=False, arrivalTime='14:20',distance=0, duration='1hr 30min'),
            'TG_921':Flight(id='TG_921', departureAirport='FRA', departureTerminal='', arrivalAirport='HKT', arrivalTerminal='', departureTime='15:05', isOverNight=True, arrivalTime='09:20',distance=0, duration='12hr 15min'),
            'TG_222':Flight(id='TG_222', departureAirport='HKT', departureTerminal='', arrivalAirport='BKK', arrivalTerminal='', departureTime='10:10', isOverNight=False, arrivalTime='11:35',distance=0, duration='1hr 25min'),
            'TG_916':Flight(id='TG_916', departureAirport='BKK', departureTerminal='', arrivalAirport='LHR', arrivalTerminal='', departureTime='13:50', isOverNight=False, arrivalTime='19:35',distance=0, duration='12hr 45min'),
            'SQ_5053':Flight(id='SQ_5053', departureAirport='HKT', departureTerminal='', arrivalAirport='SIN', arrivalTerminal='', departureTime='14:55', isOverNight=False, arrivalTime='17:40',distance=0, duration='1hr 45min'),
            'SQ_322':Flight(id='SQ_322', departureAirport='SIN', departureTerminal='', arrivalAirport='LHR', arrivalTerminal='', departureTime='23:20', isOverNight=True, arrivalTime='05:50',distance=0, duration='14hr 30min'),
            }

def getAirports():
    return {
            'LHR':Airport(id='LHR', displayName='Heathrow Airport', city_id='london'),
            'LGW':Airport(id='LGW', displayName='Gatwick Airport', city_id='london'),
            'LCY':Airport(id='LCY', displayName='London City Airport', city_id='london'),
            'LTN':Airport(id='LTN', displayName='Luton Airport', city_id='london'),
            'STN':Airport(id='STN', displayName='Stansted Airport', city_id='london'),
            'BVA':Airport(id='BVA', displayName='Beauvais-Tille Airport', city_id='paris'),
            'CDG':Airport(id='CDG', displayName='Charles De Gaulle Airport', city_id='paris'),
            'ORY':Airport(id='ORY', displayName='Orly Airport', city_id='paris'),
            'HKT':Airport(id='HKT', displayName='Phuket International Airport', city_id='phuket'),
            'BKK':Airport(id='BKK', displayName='Don Muang International Airport', city_id='bangkok'),
            'FRA':Airport(id='FRA', displayName='Frankfurt International Airport', city_id='frankfurt'),
            'SIN':Airport(id='SIN', displayName='Changi International Airport', city_id='singapore'),
            }

def getAirLines():
    return {
            'LH':Airline(id='Lufthansa', displayName='LH', flightClass=_flightClass),
            'KL':Airline(id='KLM', displayName='KL', flightClass=_flightClass),
            'AF':Airline(id='Air France', displayName='AF', flightClass=_flightClass),
            'BA':Airline(id='British Airways', displayName='BA', flightClass=_flightClass),
            'TG':Airline(id='Thai Airways International Ltd', displayName='TG', flightClass=_flightClass),
            'SQ':Airline(id='Singapore Airlines', displayName='SQ', flightClass=_flightClass),
            'MH':Airline(id='Malaysia Airlines', displayName='MH', flightClass=_flightClass),
            'VS':Airline(id='Virgin Atlantic Airways', displayName='VS', flightClass=_flightClass),
            }

def getFlightFares():
    return {
            'AF_2671':FlightFare(flight_id='AF_2671',economy=49.21, business=366.24),
            'AF_1570':FlightFare(flight_id='AF_1570',economy=49.21, business=366.24),
            'AF_5021':FlightFare(flight_id='AF_5021',economy=73.34, business=371.56),
            'AF_5026':FlightFare(flight_id='AF_5026',economy=73.34, business=371.56),
            'TG_917' :FlightFare(flight_id='TG_917', economy=435.25, business=1214.22),
            'TG_217' :FlightFare(flight_id='TG_217', economy=95.25, business=414.22),
            'TG_916' :FlightFare(flight_id='TG_916', economy=435.25, business=1214.22),
            'TG_222' :FlightFare(flight_id='TG_222', economy=95.25, business=414.22),
            'TG_921' :FlightFare(flight_id='TG_922', economy=458.12, business=1214.22),
            'LH_4727':FlightFare(flight_id='LH_4727',economy=103.34, business=471.56),
            'SQ_5053':FlightFare(flight_id='SQ_5053',economy=113.34, business=531.56),
            'SQ_322' :FlightFare(flight_id='SQ_322', economy=403.34, business=1371.56),
            }
def getHotels():
    return {
        'h01':Hotel(id='h01',
                    city='paris',
                    displayName='Hotel Roblin',
                    starRating='2',
                    address='6 Rue Chauveau-Lagarde, Louvre, 75008',
                    telephone='33 4856 3456',
                    fax='33 4856 3455',
                    img='hotel_paris_roblin.jpg',
                    description="The 4 Hotel Roblin is located in the heart of Paris off Place de la Madeleine. The Opera House and Champs Elysees are within a 10 minute walk. There are many theatres in the area showing a variety of shows. The Opera area is also where you`ll find the Moulin Rouge and the Folies Bergere. If shopping is what your looking for, the world famous department stores Galleries Lafayette and Printemps are just a 10 minute stroll.",
                    roomImg='room_paris_roblin.jpg',
                    roomDesc="The 76 spacious renovated rooms are decorated in a traditional Parisian style. They are all ensuite and equipped with air conditioning, wireless internet connection, TV with international channels, mini-bar, room safe and hairdryer. The hotel`s restaurant, 'R Cafe' opened in May 2005 and serves a wide selection of international cuisine."),

        'h02':Hotel(id='h02',
                    city='paris',
                    displayName='Waldorf Madeleine',
                    starRating='5',
                    address='12 Boulevard Malesherbes, Louvre, 75008 Paris',
                    telephone='33 4856 3456',
                    fax='33 4856 3455',
                    img='hotel_paris_waldorf.jpg',
                    description="The Hotel Waldolf Madeleine is in a superb location above the Louvre/ Place de la Concorde end of Avenue des Champs Elysees. As such many of Paris` most famous sights are within easy walking distance; the Musee du Louvre (whose contents famously include the Mona Lisa), Palais Royal and the Place de la Concorde itself. The exclusive boutiques of Rue de Trivoli and cafes and nightlife of the Champs-Elysees area are also close by.",
                    roomImg='room_paris_waldorf.jpg',
                    roomDesc="Most of Waldorf Madeleine's rooms are equipped with ensuite facilities, TV with cable and satellite channels, air conditioning. The hotel has a bar and WIFI internet access is also available. There are plenty of restaurants within minute`s walk of the hotel. The rooms are recently refurbished in brightly coloured fabrics with contemporary furniture and flat screen televisions."),

        'h03':Hotel(id='h03',
                    city='phuket',
                    displayName='Serene Resort',
                    starRating='2',
                    address='175 Koktanode Rd, Kata Beach',
                    telephone='33 4856 3456',
                    fax='33 4856 3455',
                    img='hotel_phuket_serena.jpg',
                    description="The Serene Resort &amp; Spa at the heart of the Andaman Sea on Thailand's Phuket Island is enveloped by a tropical rain forest, a perfect retreat for couples on romantic holidays, sun and sand worshipers, and travelers on weekend getaways. Visitors can stroll less than a kilometer to Karon Beach and frolic in the white sand while marveling at gorgeous sunsets. Shoppers can browse for handmade crafts at Kata Center near the hotel, while the sights of downtown Phuket are 20 minutes away.",
                    roomImg='room_phuket_serena.jpg',
                    roomDesc="Guests right out of the spa can then melt into the 92 guestrooms festooned with tropical plants and southern Thai decor. Families needing extra space can book connecting rooms, while three honeymoon suites are ideal for romantic couples. All rooms feature air- conditioning, balconies, minibars, refrigerators and wireless Internet access."),

        'h04':Hotel(id='h04',
                    city='phuket',
                    displayName='Crowne Plaza Resort',
                    starRating='5',
                    address='509 patak road Phuket 83100',
                    telephone='33 4856 3456',
                    fax='33 4856 3455',
                    img='hotel_phuket_CrownePlazaResort.jpg',
                    description='Crowne Plaza Karon Beach Phuket is bordered by tropical Karon Beach and is located five miles from Chalong Temple and approximately 27 miles from Phuket International Airport. This location is also within walking distance of the Karon Entertainment District, five miles from Patong Beach, eight miles from the Phuket Sea Shell Museum, 10 miles from Phuket Fantasea, 13 miles from Bang Pae Waterfalls, and 25 miles from Phi Phi Island.',
                    roomImg='room_phuket_CrownePlazaResort.jpg',
                    roomDesc="All rooms feature high-speed Internet access, satellite TV, in-room movies, bathrobes, coffeemakers, minibars, safes, voicemail, individual climate control, irons and ironing boards, and hairdryers. The villas feature sundecks, outdoor rainforest showers, and sunken plunge pools."),
        }

def getRooms():
    return{
        'r011':Room(id='r011',hotel='h01',type='single',capacity=1,hasBreakfast=True, price=45),
        'r012':Room(id='r012',hotel='h01',type='double',capacity=2,hasBreakfast=False, price=90),
        'r021':Room(id='r021',hotel='h02',type='single',capacity=1,hasBreakfast=False, price=65),
        'r022':Room(id='r022',hotel='h02',type='double',capacity=2,hasBreakfast=False, price=120),
        'r031':Room(id='r031',hotel='h03',type='single',capacity=1,hasBreakfast=True, price=45),
        'r032':Room(id='r032',hotel='h03',type='double',capacity=2,hasBreakfast=False, price=90),
        'r041':Room(id='r041',hotel='h04',type='single',capacity=1,hasBreakfast=False, price=65),
        'r042':Room(id='r042',hotel='h04',type='double',capacity=2,hasBreakfast=False, price=120),
        }

flights = getFlights()
ticketfares=getFlightFares()
airlines = getAirLines()
airports = getAirports()
cities = getCities()
hotels = getHotels()
rooms = getRooms()

class OneWayTrip:
    def __init__(self, departureDate, flight1_id, flight2_id=None, flightClass='economy',isOutbound=True):
        self.isRoundTrip = False
        self.departureDate = departureDate
        self.flight1_id = flight1_id
        self.flight2_id = flight2_id
        self.flightClass = flightClass
        if flight2_id is not None: needTransfer = True
        else: needTransfer = False
        self.needTransfer = needTransfer
        assert isTransferable(flight1_id, flight2_id), 'Cannot transfer from flight1 %s to flight2 %s .' %(flight1_id, flight2_id)
        self.fare = self.getFare()
        self.isOutbound = isOutbound
    def __str__(self):
        flightInfo1 = flights[self.flight1_id].__str__()
        flightInfo2 = ''
        if self.needTransfer:
            flightInfo2 = flights[self.flight2_id].__str__()
        return self.departureDate+'\n'+flightInfo1+'\n'+flightInfo2
    def toXML(self):
        if self.isOutbound: id = 'outbound'
        else: id = 'inbound'
        flight1 = flights[self.flight1_id].toXML(departureDate=self.departureDate).replace('\n','\n\t')
        if self.flight2_id is not None:
            flight2 = flights[self.flight2_id].toXML(departureDate=self.getF2DDate()).replace('\n','\n\t')
            xml = '\n\t'.join(['<trip id="%s" needTransfer="yes">' %id, flight1, flight2])+'\n'+'</trip>'
        else:
            xml = '\n\t'.join(['<trip id="%s" needTransfer="no">' %id, flight1])+'\n'+'</trip>'
        return xml
    def getFare(self):
        f1_id=self.flight1_id
        f2_id=self.flight2_id
        if f2_id is None:
            f2_id = f1_id
        f1_fares=ticketfares[f1_id]
        f2_fares=ticketfares[f2_id]
        assert self.flightClass in f1_fares, "Flight %s doesn't have class %s" %(f1_id, f1_class)
        assert self.flightClass in f2_fares, "Flight %s doesn't have class %s" %(f2_id, f2_class)
        if f1_id == f2_id:
            return f1_fares[self.flightClass]
        else:
            return 0.9*(f1_fares[self.flightClass]+f2_fares[self.flightClass])
    #need rewrite
    def getF2DDate(self):
        dd=self.departureDate
        dl=list(map(int,dd.split('-')))
        d1=date(dl[0],dl[1],dl[2])
        if flights[self.flight1_id].isOverNight:
            d2=d1+timedelta(days=1)
            return d2.strftime('%Y-%m-%d')
        else: return dd


class RoundTrip:
    def __init__(self, outboundTrip, inboundTrip):
        self.outboundTrip = outboundTrip
        self.inboundTrip = inboundTrip
        self.isRoundTrip = True
        self.fare = self.getFare()
        self.departureDate = outboundTrip.departureDate
        self.returnDate = inboundTrip.departureDate
        self.flightClass = outboundTrip.flightClass
    def __str__(self):
        print(self.outboundTrip)
        print(self.inboundTrip)
    def getFare(self):
        d_fare=self.outboundTrip.getFare()
        r_fare=self.inboundTrip.getFare()
        fare = 0.8*(d_fare+r_fare)
        return fare
    def toXML(self):
        dXML=self.outboundTrip.toXML()
        rXML=self.inboundTrip.toXML()
        xml = dXML + '\n' + rXML
        return xml

class AirTicket:
    def __init__(self, trip):
        self.trip = trip
        if isinstance(trip, OneWayTrip):
            self.isRoundTrip = False
            self.departureDate = trip.departureDate
            self.returnDate = ''
            self.flightClass = trip.flightClass
            self.fare = trip.fare
        elif isinstance(trip, RoundTrip):
            self.isRoundTrip = True
            self.departureDate = trip.departureDate
            self.returnDate = trip.returnDate
            self.flightClass = trip.flightClass
            self.fare = trip.fare
        else: raise TypeError("OneWayJourney or RoundTrip expected, but %s got" % trip)
        self.id = self.genTicketID()
    def genTicketID(self):
        departureDate = self.departureDate.replace('-','')
        if self.isRoundTrip:
            returnDate = self.returnDate.replace('-','')
            outBoundTrip = self.trip.outboundTrip
            inBoundTrip = self.trip.inboundTrip
            if  inBoundTrip.flight2_id is None: inBound_id = inBoundTrip.flight1_id
            else: inBound_id = inBoundTrip.flight1_id + '-' + inBoundTrip.flight2_id
        else:
            returnDate = ''
            outBoundTrip = self.trip
            inBound_id = ''
        if  outBoundTrip.flight2_id is None: outBound_id = outBoundTrip.flight1_id
        else: outBound_id = outBoundTrip.flight1_id + '-' + outBoundTrip.flight2_id
        if self.flightClass == 'economy': class_id = 'e'
        else: class_id = 'b'
        ticket_id = '*'.join([departureDate, outBound_id, returnDate, inBound_id, class_id])
        return ticket_id

    def toXML(self):
        isRoundTrip = '<isRoundTrip>'+str(self.isRoundTrip)+'</isRoundTrip>'
        departureDate = '<departureDate>'+self.departureDate+'</departureDate>'
        returnDate = '<returnDate>'+self.returnDate+'</returnDate>'
        flightClass = '<flightClass>'+self.flightClass+'</flightClass>'
        fare = '<fare>'+str(self.fare)+'</fare>'
        trip = self.trip.toXML().replace('\n','\n\t')
        xml = '\n\t'.join(['<airTicket id="%s">' %self.id, isRoundTrip, departureDate, returnDate, flightClass, fare, trip])+'\n'+'</airTicket>'
        return xml

def searchFlightsByCity(departureCity_id, arrivalCity_id):
    departureAirports=[]
    arrivalAirports=[]
    result={}
    for airport_id in list(airports.keys()):
        if airports[airport_id]['city_id'] == departureCity_id:
            departureAirports.append(airport_id)
        if airports[airport_id]['city_id'] == arrivalCity_id:
            arrivalAirports.append(airport_id)
##  print departureAirports
##  print arrivalAirports
    for a in departureAirports:
        for b in arrivalAirports:
            r=(searchFlightsByAirport(a, b))
            key=a+'-->'+b
            if len(r)>0:
                result[key]=r
    return result

def searchAirportsByCity(city_id):
    result=[]
    for airport_id in list(airports.keys()):
        if airports[airport_id]['city_id'] == city_id:
            result.append(airport_id)
    return result

def searchFlightsByAirport(departureAirport, arrivalAirport):
    result = []
    for f1_id in list(flights.keys()):
        for f2_id in list(flights.keys()):
            if flights[f1_id]['departureAirport']==departureAirport and flights[f2_id]['arrivalAirport']==arrivalAirport and isTransferable(f1_id, f2_id):
                if f1_id == f2_id: result.append(f1_id)
                else: result.append((f1_id, f2_id))
    return result

def searchFlights(departure, arrival):
    result={}
    departureAirports=[]
    arrivalAirports=[]
    if departure.upper() in list(airports.keys()):
        departureAirports.append(departure.upper())
    elif departure.lower() in list(cities.keys()):
        departureAirports = searchAirportsByCity(departure.lower())
    else: raise ValueError("City/Airport %s doesn't exist" % departure)
    if arrival.upper() in list(airports.keys()):
        arrivalAirports.append(arrival.upper())
    elif arrival.lower() in list(cities.keys()):
        arrivalAirports = searchAirportsByCity(arrival.lower())
    else: raise ValueError("City/Airport %s doesn't exist" % arrival)
    for a in departureAirports:
        for b in arrivalAirports:
            r=(searchFlightsByAirport(a, b))
            key=a+'-->'+b
            if len(r)>0:
                result[key]=r
    return result


def isTransferable(f1_id, f2_id=None):
    if f2_id is None or f1_id == f2_id:
        return True
    else:
        try: flight1=flights[f1_id]
        except KeyError:
            print("Flight %s doesn't exist." %f1_id)
            return False
        try: flight2=flights[f2_id]
        except KeyError:
            print("Flight %s doesn't exist." %f2_id)
            return False
        if flight1['arrivalAirport'] == flight2['departureAirport'] and flight1['arrivalTime'] < flight2['departureTime']:
            return True
        else: return False

def getTicketsXML(departure,arrival,oDate,rDate,flightClass='economy',isRoundTrip=False):
    outRoutes=searchFlights(departure,arrival)
    result=[]
    result.append('<tickets>')
    if not isRoundTrip:
        for item in list(outRoutes.items()):
            for t in item[1]:
                if isinstance(t,tuple):
                    ticket=AirTicket(OneWayTrip(oDate,t[0],t[1]))
                else:
                    ticket=AirTicket(OneWayTrip(oDate, t))
                xml=ticket.toXML().replace('\n','\n\t')
                result.append(xml)
    else:
        inRoutes=searchFlights(arrival, departure)
        for outItem in list(outRoutes.items()):
            for ot in outItem[1]:
                for inItem in list(inRoutes.items()):
                    for it in inItem[1]:
                        if isinstance(ot,tuple):
                            oTrip=OneWayTrip(oDate,ot[0],ot[1],flightClass=flightClass)
                        else:
                            oTrip=OneWayTrip(oDate, ot, flightClass=flightClass)
                        if isinstance(it,tuple):
                            iTrip=OneWayTrip(rDate,it[0],it[1],flightClass=flightClass,isOutbound=False)
                        else:
                            iTrip=OneWayTrip(rDate,it,flightClass=flightClass,isOutbound=False)
                        trip = RoundTrip(oTrip, iTrip)
                        ticket = AirTicket(trip)
                        xml=ticket.toXML().replace('\n','\n\t')
                        result.append(xml)
    return '\n\t'.join(result)+'\n</tickets>'

def getTicketXMLfromID(ticket_id):
    def getTripfromFlightID(ddate, flights_id, isOutbound=True):
        f_id = flights_id.split('-')
        if len(f_id)==2: trip = OneWayTrip(ddate,f_id[0],f_id[1],flightClass,isOutbound)
        else: trip = OneWayTrip(ddate,f_id[0],None,flightClass,isOutbound)
        return trip
    def fdate(yyyymmdd):
        return '-'.join([yyyymmdd[0:4],yyyymmdd[4:6],yyyymmdd[6:8]])
    [dd,dFlights,rd,rFlights,fc]=ticket_id.split('*')
    departureDate=fdate(dd)
    returnDate=fdate(rd)
    if fc == 'e':
        flightClass = 'economy'
    elif fc == 'b':
        flightClass = 'business'
    oTrip = getTripfromFlightID(departureDate, dFlights, True)
    if returnDate == '--': isRoundTrip = False
    else: isRoundTrip = True
    if isRoundTrip:
        iTrip = getTripfromFlightID(returnDate, rFlights, False)
        trip = RoundTrip(oTrip,iTrip)
        ticket = AirTicket(trip)
    else: ticket = AirTicket(oTrip)
    return '<tickets>\n\t' + ticket.toXML().replace('\n','\n\t') + '\n</tickets>'


def getHotelsXML(location, iDate, oDate):
    if location.upper() in list(airports.keys()):
        city=airports[location.upper()]['city_id']
    elif location.lower() in list(cities.keys()):
        city=location.lower()
    else: raise ValueError("City/Airport %s doesn't exist" %location)
    iDate = '<checkinDate>'+iDate+'</checkinDate>'
    oDate = '<checkoutDate>'+oDate+'</checkoutDate>'
    hotelList=[]
    for (id, hotel) in list(hotels.items()):
        if hotel['city']==city:
            hotelList.append(hotel.toXML().replace('\n','\n\t'))
    hotelXML='\n\t'.join(hotelList)
    xml = '\n\t'.join(['<hotels>',iDate,oDate,hotelXML])+'\n'+'</hotels>'
    return xml

def getAccommodationPrice(room_id,numOfNights,numOfAdults):
    room=rooms[room_id]
    pricePerNight=int(room['price'])
    capacity=int(room['capacity'])
    numOfRooms = numOfAdults/capacity
    if numOfAdults%capacity!=0:
        numOfRooms+=1
    total = numOfNights*numOfRooms*pricePerNight
    return total, numOfRooms

def dateSubtraction(date1,date2):
    #date1 and date2 are in the formate of 'yyyy-mm-dd'
    def getDObject(ymd):
        y=int(ymd[0:4])
        m=int(ymd[5:7])
        d=int(ymd[8:10])
        return date(y,m,d)
    d1=getDObject(date1)
    d2=getDObject(date2)
    return (d2-d1).days

def getHotelXMLfromCode(hotelCode):
    [iDate,oDate,rid,numOfAdults] = hotelCode.split('*')
    def formatDate(ymd):
        y=ymd[0:4]
        m=ymd[4:6]
        d=ymd[6:8]
        return '-'.join([y,m,d])
    numOfNights=dateSubtraction(formatDate(iDate),formatDate(oDate))
    (cost, numOfRooms)= getAccommodationPrice(rid,numOfNights,int(numOfAdults))
    iDateXML = '<checkinDate>'+formatDate(iDate)+'</checkinDate>'
    oDateXML = '<checkoutDate>'+formatDate(oDate)+'</checkoutDate>'
    total ='<cost>'+str(cost)+'</cost>'
    rn = '<numOfRooms>'+str(numOfRooms)+'</numOfRooms>'
    hid = 'h'+rid[1:3]
    hotelXML = hotels[hid].toXML(room_id=rid)
    xml = '\n\t'.join([i.replace('\n','\n\t') for i in ['<hotels>',iDateXML,oDateXML,total,rn,hotelXML]])+'\n</hotels>'
    return xml

def getPresaleXML(tripTitle,subtitle,customerName,orig, dest,oDate,rDate,flightClass,isRoundTrip):
    ticketsXML = getTicketsXML(orig, dest,oDate=oDate,rDate=rDate,flightClass=flightClass,isRoundTrip=isRoundTrip).replace('\n','\n\t')
    hotelsXML=getHotelsXML(dest,oDate,rDate).replace('\n','\n\t')
    def getCity(dd):
        if dd in list(airports.keys()): return airports[dd]['city_id']
        if dd.lower() in list(cities.keys()): return dd.lower()
    tripTitleXML='<tripTitle>'+tripTitle+'</tripTitle>'
    subtitleXML='<subtitle>'+subtitle+'</subtitle>'
    customerXML='<customerName>'+customerName+'</customerName>'
    cityInfoXML= cities[getCity(dest)].toXML().replace('\n','\n\t')
    xml = '\n\t'.join(['<presale>',tripTitleXML,subtitleXML,customerXML,ticketsXML,hotelsXML,cityInfoXML])+'\n</presale>'
    return xml

def getStep2XML(orig, dest, oDate, rDate, ticket_id):
    ticketsXML = getTicketXMLfromID(ticket_id)
    hotelsXML=getHotelsXML(dest,oDate,rDate).replace('\n','\n\t')
    xml = '\n\t'.join(['<step2>',ticketsXML,hotelsXML])+'\n</step2>'
    return xml

def getStep3XML(orig, dest, checkinDate, checkoutDate, ticket_id, hotel_id):
    ticketsXML = getTicketXMLfromID(ticket_id)
    iDateXML = '<checkinDate>'+checkinDate+'</checkinDate>'
    oDateXML = '<checkoutDate>'+checkoutDate+'</checkoutDate>'
    hotelsXML = '\n\t'.join(['<hotels>',iDateXML,oDateXML,hotels[hotel_id].toXML().replace('\n','\n\t')])+'\n</hotels>'
    xml = '\n\t'.join(['<step3>',ticketsXML,hotelsXML])+'\n</step3>'
    return xml

def getStep4XML(tripTitle,subtitle,customerName,ticket_id,roomBooking_id):
    tripTitleXML='<tripTitle>'+tripTitle+'</tripTitle>'
    subtitleXML='<subtitle>'+subtitle+'</subtitle>'
    customerXML='<customerName>'+customerName+'</customerName>'
    ticketsXML = getTicketXMLfromID(ticket_id).replace('\n','\n\t')
    hotelsXML = getHotelXMLfromCode(roomBooking_id).replace('\n','\n\t')
    xml = '\n\t'.join(["<itinerary>",tripTitleXML,subtitleXML,customerXML,ticketsXML,hotelsXML])+'\n</itinerary>'
    return xml
