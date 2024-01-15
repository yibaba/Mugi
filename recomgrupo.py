import requests
#from rich.progress import track
from rich.console import Console
from rich.table import Table
import time
from numbers import Number
import json
import pickle
import sys
from typing import Any, Callable, Iterator, TypeVar
#import fnmatch
import re

cooloff: float = 0.3

class tokenBearer:
    def __init__(self) -> None:
        self.token: str = ""
        self.timestamp: float = time.time()
        self.caducidad: int = 9*60

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
        getcredentials()
        print("Obteniendo token")
        time.sleep(cooloff)
        peticion_token = requests.put(
            "https://api.mangaupdates.com/v1/account/login", data=credentials.en_formato_serializable())
        if peticion_token.ok:
            token.timestamp = time.time()
            token.token = peticion_token.json()["context"]["session_token"]
            cachear_peticion(
                peticion=peticion_token,
                url="https://api.mangaupdates.com/v1/account/login")
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
    escribir_peticiones()

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
    algo_borrado: bool = False
    for peticion in peticiones:
        if peticion.linkapi == url:
            peticiones.remove(peticion)
            algo_borrado = True
    if not algo_borrado:
        print("Aviso: no se ha borrado nada")
        print(f"url analizada:\n\t{url}")

def rellenar_tabla_ids_leidos_si_necesario() -> None:
    global peticiones
    url: str = "https://api.mangaupdates.com/v1/lists/0/search"
    if comprobar_si_toca_pedir(url):
        print("tabla ids leidos no encontrada")
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
    lista_filtrada: list[peticiontempeada]|None = devolver_lista_ocurrencias_por_linkapi(
        r"^https://api\.mangaupdates\.com/v1/lists/\d+/search$")
    #consigue bien la lista filtrada
    if lista_filtrada is None:
        print("no se encuentra tal ocurrencia") 
        print("fallo al construir la lista de ids ponderados m1")
        sys.exit(13)
    lista_filtrada_iterable:Iterator[str] = lista_peticiones_a_iterator_de_propiedad(
        lista=lista_filtrada,
        propiedad="stringjson")
    for cadenajson in lista_filtrada_iterable:
        #print(f"cadenajson:\n\t{cadenajson}")
        diccionario_bucle = json.loads(cadenajson)["results"]
        for dict_serie in diccionario_bucle:
            rating = dict_serie["metadata"]["series"]["bayesian_rating"]
            rating = rating if isinstance(rating, Number) else 0
            id_serie = dict_serie["record"]["series"]["id"]
            progreso = dict_serie["record"]["status"]["chapter"] / dict_serie["metadata"]["series"]["latest_chapter"]
            # print(f"añadiendo id {elid}")
            yield (id_serie, rating*progreso)


def grupos_serie_por_id(id: int) -> set[tuple[int, str]]:
    lista_recomendados: list[peticiontempeada]|None = devolver_lista_ocurrencias_por_linkapi(
        f"^https://api.mangaupdates.com/v1/series/{id}/groups$")
    if lista_recomendados is None:
        print("no se encuentra tal ocurrencia")
        print("fallo al construir lista_recomendados")
        sys.exit(12)
    lista_recomendados_iterable: Iterator[str] = lista_peticiones_a_iterator_de_propiedad(
        lista=lista_recomendados,
        propiedad="stringjson")
    conjunto_resultado: set[tuple[int, str]] = set()
    for cadenajson in lista_recomendados_iterable:
        diccionario_bucle = json.loads(cadenajson)["group_list"]
        for diccionario_grupo in diccionario_bucle:
            id_grupo = diccionario_grupo["group_id"]
            nombre = diccionario_grupo["name"]
            conjunto_resultado.add((id_grupo, nombre))
    return conjunto_resultado

def ordenar_listatuplas(lista_tuplas: list[tuple[int, str, float]]) -> list[tuple[int, str, float]]:
    newlist = sorted(lista_tuplas, key=lambda x: x[2], reverse=True)
    return newlist

# Bastante guarra, dividir en dos
def tabla_ids_recomendados_segun_iterador_ponderador(
        funcion_ponderacion: Callable[..., Iterator[tuple[int, float]]]) -> list[tuple[int, str, float]]:
    
    dict_total_grupos: dict[int, tuple[str, float]] = {}
    for tupla in funcion_ponderacion():
        id_serie, puntos = tupla
        url = f"https://api.mangaupdates.com/v1/series/{id_serie}/groups"
        if comprobar_si_toca_pedir(url):
            peticion = hacer_peticion_get(url=url)
            if peticion.ok:
                cachear_peticion(peticion=peticion, url=url)
            else:
                print("error petición series id")
                sys.exit(peticion.status_code)
        conjunto_parcial_grupos: set[tuple[int, str]] = grupos_serie_por_id(
            id=id_serie)
        for grupo_id, nombre_grupo in conjunto_parcial_grupos:
            if grupo_id in dict_total_grupos.keys():
                nombre, a_puntos = dict_total_grupos[grupo_id]
                dict_total_grupos[grupo_id] = (nombre, a_puntos+puntos)
            else:
                dict_total_grupos.setdefault(grupo_id, (nombre_grupo, puntos))
    lista_total_grupos: list[tuple[int, str, float]] = []
    for grupo_id in dict_total_grupos.keys():
        nombre, peso = dict_total_grupos[grupo_id]
        tupla_a_sumar: tuple[int, str, float] = (grupo_id, nombre, peso)
        lista_total_grupos.append(tupla_a_sumar)
    lista_total_grupos = ordenar_listatuplas(lista_total_grupos)
    return lista_total_grupos

def iterador_top_grupos(f_grupos: Callable[..., list[tuple[int, str, float]]], num:int) -> Iterator[tuple[int, str, float]]:
    grupos_totales: list[tuple[int, str, float]] = f_grupos(
            funcion_ponderacion=iterador_tabla_ids_ponderados_m1
    )
    for tupla in grupos_totales:
        if num < 0:
            num -=1
            yield tupla
        else:
            pass

def escupir_tabla_gid_nombre_peso(it_grupos:Callable[..., Iterator[tuple[int, str, float]]], num:int) -> Any:
    tabla = Table(title="Más Recomendados")
    tabla.add_column("Nombre")
    tabla.add_column("Id")
    tabla.add_column("Peso")
    for grupo_id, nombre, peso in it_grupos(
        f_grupos=tabla_ids_recomendados_segun_iterador_ponderador,
        num=num
    ):
        idgrupo = str(grupo_id)
        puntos = str(peso)
        tabla.add_row(nombre, idgrupo, puntos)
    console = Console()
    console.print(tabla)

if __name__ == "__main__":
    leer_peticiones()
    # tanto monta
    rellenar_tabla_ids_leidos_si_necesario()
    #print(peticiones)
    numero = int(input("Numero de Resultados: "))
    escupir_tabla_gid_nombre_peso(it_grupos=iterador_top_grupos, num=numero)
    # monta tanto
    escribir_peticiones()
    sys.exit(0)
