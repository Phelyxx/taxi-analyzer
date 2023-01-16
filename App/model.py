"""
 * Copyright 2020, Departamento de sistemas y Computación
 * Universidad de Los Andes
 *
 *
 * Desarrolado para el curso ISIS1225 - Estructuras de Datos y Algoritmos
 *
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 """
import config
import operator
from datetime import datetime, timedelta, date
from DISClib.ADT import list as lt
from DISClib.ADT import map as mp
from DISClib.DataStructures import edge as e    
from DISClib.ADT import orderedmap as om
from DISClib.DataStructures import mapentry as me
from DISClib.ADT.graph import gr
from DISClib.Algorithms.Graphs import scc
from DISClib.Algorithms.Graphs import dfs
from DISClib.Algorithms.Graphs import dijsktra as djk
from DISClib.Utils import error as error
assert config


# -----------------------------------------------------
# API del TAD de Taxis
# -----------------------------------------------------


def newAnalyzer():
    """ Inicializa el analizador

    Crea una lista vacia para guardar los nombres de los taxis
    Guarda datos de las compañías en un mapa.

    """
    analyzer = {'taxis': None,
               'companies': None,
               "dateIndex": None,
               "Taxi_Trips": None}

    analyzer['taxis'] = []   
    analyzer['companies'] = mp.newMap(50,
                                   maptype='PROBING',
                                   loadfactor=0.4,
                                   comparefunction=compareCompanies)
    analyzer['dateIndex'] = om.newMap(omaptype='RBT',
                                      comparefunction=compareDates)    

    analyzer['Taxi_Trips'] = {
                    'stops': None,
                    'connections': None,
                    'components': None,
                    'paths': None,              
                    }
    analyzer['Taxi_Trips']['stops'] = mp.newMap(numelements=14000,
                                     maptype='PROBING',
                                     comparefunction=compareStopIds)

    analyzer['Taxi_Trips']['connections'] = gr.newGraph(datastructure='ADJ_LIST',
                                              directed=True,
                                              size=14000,
                                              comparefunction=compareStopIds)
    return analyzer

# Funciones para agregar informacion sobre viajes

def newCompany(name):
    """
    Crea una nueva estructura para modelar las compañías de taxis,
    su número de servicios y sus taxis afiliados
    """
    companies = {'name': "", 
              "taxis": lt.newList('SINGLE_LINKED', compareTaxiIds),
              "numservices": 0}
    companies['name'] = name
    return companies

def addTrips(analyzer, trip):
    if trip["taxi_id"] not in analyzer["taxis"]:
       analyzer["taxis"].append(trip["taxi_id"])   
    addTaxiDate(analyzer, trip)   
    companyname = trip["company"]
    if companyname == "":
       companyname = "Independent Owner" 
    companies = analyzer['companies']
    existcompany = mp.contains(companies, companyname)
    if existcompany:
        entry = mp.get(companies, companyname)
        company = me.getValue(entry)
    else:
        company = newCompany(companyname)
        mp.put(companies, companyname, company)  
    if lt.isPresent(company["taxis"], trip["taxi_id"]) == False:    
       lt.addLast(company['taxis'], trip["taxi_id"]) 
    company["numservices"] += 1


    origin= trip['pickup_community_area'].replace(" ","")
    destination= trip ['dropoff_community_area'].replace(" ","")
    if origin == None or origin == "":
        origin=0
    if destination == None or destination == "":
        destination=0
    origin = int(float(origin))
    destination = int(float(destination))

    if origin != destination:
        if trip['trip_seconds'] != "":
            duration = float(trip ['trip_seconds'])
        else:
            duration=float(0)

        oDateTime=datetime.strptime(str(trip['trip_start_timestamp']), '%Y-%m-%dT%H:%M:%S.%f')
        odt=oDateTime.time()
        odtt=odt.strftime("%H:%M")
        Corigin = str(origin)+"-"+odtt


        if trip['trip_end_timestamp'] == "":
            ndt = timedelta(seconds=int(duration))
            tempdt=datetime.strptime(str(trip['trip_start_timestamp']), '%Y-%m-%dT%H:%M:%S.%f')
            dDateTime = tempdt + ndt
        else:
            dDateTime = datetime.strptime(str(trip['trip_end_timestamp']), '%Y-%m-%dT%H:%M:%S.%f')
        ddt=dDateTime.time()
        ddtt=ddt.strftime("%H:%M")
        Cdestination =  str(destination)+"-"+ddtt

        addStop(analyzer, Corigin)
        addStop(analyzer, Cdestination)
        addConnection (analyzer, Corigin, Cdestination, duration)

def addTaxiDate(analyzer, trip):
    """
    """
    occurreddate = trip['trip_start_timestamp']
    tripdate = occurreddate[0:10]
    entry = om.get(analyzer["dateIndex"], tripdate)
    if entry is None:
       om.put(analyzer["dateIndex"], tripdate, mp.newMap(50,
                                   maptype='PROBING',
                                   loadfactor=0.4,
                                   comparefunction=compareTaxiIds))
    entry = om.get(analyzer["dateIndex"], tripdate)                   
    if mp.contains(entry["value"], trip["taxi_id"]) == False:
       taxi_data = me.getValue(entry)
       taxi_data = newTaxi(trip["taxi_id"])
       if trip["trip_miles"] != "" and trip["trip_total"] != "":
          millas = float(trip["trip_miles"])
          dinero = float(trip["trip_total"]) 
          if millas > 0 and dinero > 0:
             taxi_data["millas"] = millas
             taxi_data["dinero"] = dinero
             mp.put(entry["value"], trip["taxi_id"], taxi_data) 
    else:
       taxi_data = me.getValue(entry)
       taxi_data = mp.get(me.getValue(entry), trip["taxi_id"])
       taxi_data = taxi_data["value"]
       if trip["trip_miles"] != "" and trip["trip_total"] != "":
          millas = float(trip["trip_miles"])
          dinero = float(trip["trip_total"])  
          if millas > 0 and dinero > 0:
             taxi_data["millas"] += millas
             taxi_data["dinero"] += dinero      
             taxi_data["numservices"] += 1     
             mp.put(entry["value"], trip["taxi_id"], taxi_data) 

def newTaxi(name):
    """
    """
    taxi_data = {'name': "", 
              "millas": 0,
              "dinero": 0,
              "numservices": 1}
    taxi_data['name'] = name
    return taxi_data

def addStop(analyzer, stopid):
    """
    Adiciona una estación como un vertice del grafo
    """
    try:
        if not gr.containsVertex(analyzer['Taxi_Trips']['connections'], stopid):
            gr.insertVertex(analyzer['Taxi_Trips']['connections'], stopid)
        return analyzer
    except Exception as exp:
        error.reraise(exp, 'model:addStation')


def addConnection(analyzer, origin, destination, duration):
    """
    Adiciona un arco entre dos estaciones. Si el arco existe se actualiza su peso con el promedio.
    """
    edge = gr.getEdge(analyzer['Taxi_Trips']['connections'], origin, destination)
    if edge is None:
        gr.addEdge(analyzer['Taxi_Trips']['connections'], origin, destination, duration)
    else:
        e.updateAverageWeight(edge,duration)
    return analyzer     


# ==============================
# Funciones de consulta
# ==============================


def getTopCompanies(analyzer, numberM, numberN):
    """
    """
    companies = mp.valueSet(analyzer["companies"])
    top_taxis = {}
    top_services = {}
    for i in range(lt.size(companies)):
        company = lt.getElement(companies, i)
        top_taxis[company["name"]] = lt.size(company["taxis"])
        top_services[company["name"]] = company["numservices"]  
    top_taxis = sorted(top_taxis.items(), key=operator.itemgetter(1), reverse=True)
    top_services = sorted(top_services.items(), key=operator.itemgetter(1), reverse=True) 
    num_companias = lt.size(companies)
    num_taxis = len(analyzer["taxis"])
    res = [num_taxis, num_companias, top_taxis[0:numberM], top_services[0:numberN]]
    return res

def getTaxisPointsByRange(analyzer, initialDate, finalDate, numN):
    """
    """
    lst = om.values(analyzer['dateIndex'], initialDate, finalDate)
    dicc_taxi = {}
    for i in range(lt.size(lst)):
        date = lt.getElement(lst, i)
        for taxi_name in analyzer["taxis"]:
            taxi_data = mp.get(date, taxi_name)
            if taxi_data != None:
               millas = taxi_data["value"]["millas"]
               dinero = taxi_data["value"]["dinero"]
               numservices = taxi_data["value"]["numservices"]
               if taxi_name not in dicc_taxi:
                  dicc_taxi[taxi_name] = [millas, dinero, numservices]
               else:
                  millas2 = dicc_taxi[taxi_name][0]
                  dinero2 = dicc_taxi[taxi_name][1]
                  numservices2 = dicc_taxi[taxi_name][2]
                  dicc_taxi[taxi_name] = [millas + millas2, dinero + dinero2, numservices + numservices2]   
    for taxi_name in analyzer["taxis"]:
        if taxi_name in dicc_taxi:
           alfa = (dicc_taxi[taxi_name][0] / dicc_taxi[taxi_name][1]) * dicc_taxi[taxi_name][2]       
           dicc_taxi[taxi_name] = alfa
    top_alfa = sorted(dicc_taxi.items(), key=operator.itemgetter(1), reverse=True)   
    return top_alfa[0:numN]      

def getstationsinrange(analyzer,cao,rti,rtf):
    dti=datetime.strptime(rti, '%H:%M')
    dtii=dti.time()
    dtf=datetime.strptime(rtf, '%H:%M')
    dtff=dtf.time()
    
    index=dtii
    lph=[]
    while index <= dtff:
        lph.append(index)
        d = datetime.now()
        combineindex = datetime.combine(d, index)
        index = combineindex + timedelta(minutes=15)
        index=index.time()
    lcao=[]
    for i in lph:
        horario=i.strftime("%H:%M")
        rvertice= cao+"-"+horario
        if gr.containsVertex(analyzer['Taxi_Trips']['connections'],rvertice) is True:
            lcao.append(rvertice)
    return lcao

def getbestroute(analyzer,lcao,cad):
    lcad = getstationsinrange(analyzer,cad,"00:00","23:59")
    cmenor=10000
    lcmenores=[]
    for phora in lcao:
        for pdestino in lcad:
            mCostPath = float(djk.distTo(phora,pdestino))
            if mCostPath < cmenor:
                cmenor = mCostPath
        lcmenores.append(cmenor)
    cminimo=min(lcmenores)
    posicion=lcmenores.index(cminimo)
    elvertice=lcao[posicion]
    return elvertice
    

def minimumCostPaths(analyzer, initialStation):
    """
    Calcula los caminos de costo mínimo desde la estacion initialStation
    a todos los demas vertices del grafo
    """
    analyzer['Taxi_Trips']['paths'] = djk.Dijkstra(analyzer['Taxi_Trips']['connections'], initialStation)
    return analyzer

def minimumCostPath(analyzer, destStation):
    """
    Retorna el camino de costo minimo entre la estacion de inicio
    y la estacion destino
    Se debe ejecutar primero la funcion minimumCostPaths
    """
    path = djk.pathTo(analyzer['Taxi_Trips']['paths'], destStation)
    return path

# ==============================
# Funciones de Comparacion
# ==============================


def compareTaxiIds(id1, id2):
    """
    Compara dos ids de taxis
    """
    if not isinstance(id2, str):
       id2 = me.getKey(id2)
    if (id1 == id2):
        return 0
    elif id1 > id2:
        return 1
    else:
        return -1


def compareCompanies(id, entry):
    """
    Compara dos compañías
    """
    identry = me.getKey(entry)
    if id == identry:
        return 0
    elif id > identry:
        return 1
    else:
        return -1

def compareDates(date1, date2):
    """
    Compara dos fechas
    """
    if (date1 == date2):
        return 0
    elif (date1 > date2):
        return 1
    else:
        return -1        

def compareTrips(trip1, route2):
    """
    Compara dos rutas
    """
    trip2=route2['key']
    if (trip1 == trip2):
        return 0
    elif (trip1 > trip2):
        return 1
    else:
        return -1

def compareStopIds(stop, keyvaluestop):
    """
    Compara dos estaciones
    """
    stopcode = keyvaluestop['key']
    if (stop == stopcode):
        return 0
    elif (stop > stopcode):
        return 1
    else:
        return -1