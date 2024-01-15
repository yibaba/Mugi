import requests
#from rich.progress import track
#from rich.console import Console
#from rich.table import Table
import time
from numbers import Number
import json
import pickle
import sys
from typing import Any, Callable, Iterable, Iterator, TypeVar, cast
#import fnmatch
import re

cooloff: float = 0.3

class tokenBearer:
    def __init__(self) -> None:
        self.token: str = ""
        self.timestamp: float = time.time()
        self.caducidad: int = 60*60

class credenciales:
    def __init__(self) -> None:
        self.user: str = ""
        self.passw: str = ""

    def en_formato_serializable(self) -> dict[str, str]:
        diccionario: dict[str, str] = {}
        diccionario.setdefault("username", self.user)
        diccionario.setdefault("password", self.passw)
        return diccionario

class peticiontempeada:
    def __init__(self) -> None:
        self.linkapi: str = ""
        self.stringjson: str  = "{}"
        self.timestamp: float = time.time()
        self.caducidad: int = 60*60

peticiones: list[peticiontempeada] = []

def escribir_peticiones() -> None:
    print("Escribiendo...")
    with open("peticiones", "wb") as peticiones_f:
        pickle.dump(peticiones, peticiones_f)

def leer_peticiones() -> None:
    print("Leyendo...")
    with open("peticiones", "rb") as peticiones_f:
        global peticiones
        peticiones_temp = pickle.load(peticiones_f)
        if peticiones_temp != 0:
            print("Exito cargando peticiones")
            peticiones = peticiones_temp
        else:
            print("fallo en la carga")
            sys.exit(69)


credentials = credenciales()
def getcredentials() -> None:
    credentials.user = input("Usuario: ")
    credentials.passw = input("Contraseña: ")



clases_timestampleables = TypeVar('clases_timestampleables', tokenBearer, peticiontempeada)
def timestamp_caducada(clase: clases_timestampleables) -> bool:
    if time.time()-clase.timestamp>=clase.caducidad:
        return True
    return False

token = tokenBearer()

def refrescar_token_si_necesario() -> None:
    global token
    if token.token == "" or timestamp_caducada(token):
        print("Obteniendo token")
        time.sleep(cooloff)
        peticion_token = requests.put(
            "https://api.mangaupdates.com/v1/account/login", data=credentials.en_formato_serializable())
        if peticion_token.ok:
            token.timestamp = time.time()
            token.token = peticion_token.json()["context"]["session_token"]
        else:
            statcode = f"Código de estatus: {peticion_token.status_code}"
            print("error al conseguir el token")
            print(statcode)
            print("Texto:")
            print(peticion_token.text)

def getheader() -> dict[str, str]:
    refrescar_token_si_necesario()
    secreto = f"Bearer {token.token}"
    return {"Authorization": secreto,
            "Content-Type": "application/json"}



def cachear_peticion(peticion:requests.Response, url:str) -> None:
    limpiar_url_de_peticiones(url=url)
    listado = peticiontempeada()
    listado.linkapi = url
    listado.stringjson = peticion.text
    peticiones.append(listado)

def hacer_peticion_get(url: str) -> requests.Response:
    global cooloff
    time.sleep(cooloff)
    hdr = getheader()
    return requests.get(url=url, headers=hdr)


def hacer_peticion_post(url: str, cont: str) -> requests.Response:
    global cooloff
    time.sleep(cooloff)
    hdr = getheader()
    return requests.post(url=url, data=cont, headers=hdr)

def comprobar_si_toca_pedir(enlace: str) -> bool:
    global peticiones
    en_lista_peticiones = False
    for s_peticion in peticiones:
        if s_peticion.linkapi == enlace:
            en_lista_peticiones = True
            if timestamp_caducada(s_peticion):
                return True
    return not en_lista_peticiones

def limpiar_url_de_peticiones(url: str) -> None:
    print(f"limpiando url: \n\t {url}")
    algo_borrado_flag = True
    for peticion in peticiones:
        if peticion.linkapi == url:
            peticiones.remove(peticion)
            algo_borrado_flag = False
    if algo_borrado_flag:
        print("fallo al limpiar la siguiente url linkapi:")
        print(f"\t{url}")
        sys.exit(31)

def rellenar_tabla_ids_leidos_si_necesario() -> None:
    global peticiones
    url: str = "https://api.mangaupdates.com/v1/lists/0/search"
    if comprobar_si_toca_pedir(url):
        print("tabla ids leidos encontrada")
        longitud: dict[str, int] = {"page": 1,
         "perpage": 1000}
        cont: str = json.dumps(longitud)
        peticion: requests.Response = hacer_peticion_post(url=url, cont=cont)
        if peticion.ok:
            cachear_peticion(peticion=peticion, url=url)
        else:
            print("error petición tabla ids")
            sys.exit(peticion.status_code)

def devolver_lista_ocurrencias_por_linkapi(expr:str) -> list[peticiontempeada]|None:
    r = re.compile(expr)
    indices: list[peticiontempeada] = []
    for peticion in filter(lambda x: r.match(x.linkapi), peticiones):
        indices.append(peticion)
    if not indices:
        return None
    return indices

def lista_peticiones_a_iterator_de_propiedad(lista:list[peticiontempeada], propiedad:str) -> Iterator[Any]:
    for peticion in lista:
        valor_propiedad = getattr(peticion, propiedad)
        yield valor_propiedad

def iterador_tabla_ids_ponderados_m1() -> Iterator[tuple[int, float]]:
    # https://api\.mangaupdates\.com/v1/lists/\d+/search$
    lista_filtrada: list[peticiontempeada]|None = devolver_lista_ocurrencias_por_linkapi(
        r"^https://api\.mangaupdates\.com/v1/lists/\d+/search$")
    if lista_filtrada is None:
        print("no se encuentra tal ocurrencia") 
        print("fallo al construir la lista de ids ponderados m1")
        sys.exit(13)
    lista_filtrada_iterable:Iterator[str] = lista_peticiones_a_iterator_de_propiedad(
        lista=lista_filtrada,
        propiedad="linkapi")
    for cadenajson in lista_filtrada_iterable:
        diccionario_bucle = json.loads(cadenajson)
        rating = diccionario_bucle["metadata"]["series"]["bayesian_rating"]
        rating = rating if isinstance(rating, Number) else 0
        id_serie = diccionario_bucle["record"]["series"]["id"]
        progreso = diccionario_bucle["metadata"]["series"]["latest_chapter"] / diccionario_bucle["record"]["status"]["chapter"]
        # print(f"añadiendo id {elid}")
        yield (id_serie, rating*progreso)

# Dividir en tres, el que hace la petición, el iterador y el orquestrador que escupe la lista ordenada
def tabla_ids_recomendados_segun_iterador_ponderador(
        funcion_ponderación: Callable[..., Iterator[tuple[int, float]]]) -> set[tuple[str, int, float]]:

    workingset: set[int] = set()
    repetidos: list[int] = []
    conjunto_series: set[tuple[str, int, float]]
    for tupla in funcion_ponderación():
        id_serie, puntos = tupla
        url = f"https://api.mangaupdates.com/v1/series/{id_serie}/groups"
        if comprobar_si_toca_pedir(url):
            peticion = hacer_peticion_get(url=url)
            if peticion.ok:
                cachear_peticion(peticion=peticion, url=url)
            else:
                print("error petición series id")
                sys.exit(peticion.status_code)


if __name__ == "__main__":
    #leer_peticiones()
    # tanto monta
    getcredentials()
    rellenar_tabla_ids_leidos_si_necesario()
    print(peticiones)
    # monta tanto
    escribir_peticiones()
    sys.exit(0)
"""
tCadRecs = 60*60
thrTime = 0.3
credentials = {}


def getcredentials():
    credentials.setdefault("username", input("Usuario: "))
    credentials.setdefault("password", input("Contraseña: "))


class tokenobj:
    def __init__(self):
        self.token = ""
        self.timestamp = 0.0


class idtable:
    def __init__(self):
        self.dic = {}
        self.timestamp = 0.0


def getheader():
    tokenacq()
    secreto = f"Bearer {token.token}"
    return {"Authorization": secreto,
            "Content-Type": "application/json"}


token = tokenobj()
losids = idtable()
recids = idtable()
# recargar objeto token


def tokenacq():
    if token.token == "" or time.time()-token.timestamp >= 3500:
        print("Obteniendo token")
        time.sleep(thrTime)
        locreq = requests.put(
            "https://api.mangaupdates.com/v1/account/login", data=credentials)
        if locreq.ok:
            token.timestamp = time.time()
            token.token = locreq.json()["context"]["session_token"]
        else:
            print("error al conseguir el token")


def idstable():
    if not losids.dic or time.time()-losids.timestamp >= tCadRecs:
        hdr = getheader()
        cont = {"page": 1,
                "perpage": 1000}
        cont = json.dumps(cont)
        url = "https://api.mangaupdates.com/v1/lists/0/search"
        time.sleep(thrTime)
        lstallentpy = requests.post(
            url=url, data=cont, headers=hdr)
        if lstallentpy.ok:
            print("obteniendo lista")
            for dicto in track(lstallentpy.json()["results"],
                               description="Trabajando..."):
                rat = dicto["metadata"]["series"]["bayesian_rating"]
                rat = rat if isinstance(rat, numbers.Number) else 0
                elid = dicto["record"]["series"]["id"]
                progr = dicto["metadata"]["series"]["latest_chapter"] / dicto["record"]["status"]["chapter"]
                # print(f"añadiendo id {elid}")
                # losids.dic.setdefault(elid, rat*progr)
                if elid in losids.dic.keys():
                    losids.dic[elid] = rat*progr
                else:
                    losids.dic.setdefault(elid, rat*progr)
        else:
            print("error al conseguir la lista")
            print(f"hdr {hdr}")
            print(f"content {lstallentpy.content}")
        print("actualizando tiempos")
        losids.timestamp = time.time()


def rectable():
    if not recids.dic or time.time()-recids.timestamp >= tCadRecs:
        for llave in track(losids.dic.keys(), description="Procesando..."):
            url = f"https://api.mangaupdates.com/v1/series/{llave}/groups"
            hdr = getheader()
            time.sleep(thrTime)
            lreq = requests.get(url=url, headers=hdr)
            print("OtL")
            if lreq.ok:
                for serreq in lreq.json()["group_list"]:
                    miid = serreq["name"]
                    print("InL")
                    peso = losids.dic[llave]
                    # print(f"procesando {miid}")
                    if miid in recids.dic.keys():
                        recids.dic[miid] += peso
                    else:
                        recids.dic.setdefault(miid, peso)
            else:
                print("error al conseguir la reclista")
        print("actualizando tiempos")
        recids.timestamp = time.time()


def logout():
    hdr = getheader()
    _ = requests.post(
        "https://api.mangaupdates.com/v1/account/logout", headers=hdr)


def orderdict(dic):
    newtup = sorted(dic.items(), key=lambda x: x[1], reverse=True)
    newdic = dict(newtup)
    return newdic


def getdatatops(numb):
    tabla = Table(title="Más Recomendadas")
    tabla.add_column("Nombre")
    tabla.add_column("Peso")
    for elid in track(recids.dic.keys(), description="Ensamblando..."):
        if numb > 0:
            titulo = str(elid)
            peso = str(recids.dic[elid])
            tabla.add_row(titulo, peso)
            numb -= 1
        else:
            pass
    console = Console()
    console.print(tabla)


def loadids():
    with open("losids", "rb") as losids_f:
        global losids
        tlosids = pickle.load(losids_f)
        if tlosids != 0:
            print("Exito cargando ids")
            losids = tlosids
    with open("grids", "rb") as recids_f:
        global recids
        trecids = pickle.load(recids_f)
        if trecids != 0:
            print("Exito cargando recids")
            recids = trecids


def dumpids():
    with open("losids", "wb") as losids_f:
        pickle.dump(losids, losids_f)
    with open("grids", "wb") as recids_f:
        pickle.dump(recids, recids_f)


if __name__ == "__main__":
    #loadids()
    print(time.gmtime(losids.timestamp))
    print(time.gmtime(recids.timestamp))
    print(time.gmtime(time.time()))
    # sys.exit(1)
    getcredentials()
    idstable()
    rectable()
    recids.dic = orderdict(recids.dic)
    getdatatops(int(input(f"Numero de resultados de {len(recids.dic)}: ")))
    logout()
    dumpids()
    exit(0)
"""
