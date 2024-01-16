import requests
#from rich.progress import track
from rich.console import Console
from rich.table import Table
import time
from numbers import Number
import json
import pickle
import sys
from typing import Any, Callable, Iterator, Type, TypeAlias, TypeVar, cast
#import fnmatch
import re
from random import randint

cooloff: float = 0.5

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
        self.caducidad: int = (12*60*60)+randint(1, 120)

despido:str = "現在我有冰淇淋\n我很喜歡冰淇淋\n但是\n《速度與激情9》\n比冰淇淋\n《速度與激-》\n《速度與激情9》\n我最喜歡\n所以現在是\n音樂時間\n準備\n\n一\n二\n三\n\n兩個禮拜以後\n《速度與激情9》\n兩個禮拜以後\n《速度與激情9》\n兩個禮拜以後\n《速度與激情9》\n\n不要忘記\n不要錯過\n去電影院\n看《速度與激情9》\n因為非常好電影\n動作非常好\n差不多一樣「冰激淋」\n再見"

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



def cachear_peticion(peticion:requests.Response, url:str, caducidad:int=-1) -> None:
    limpiar_url_de_peticiones(url=url)
    listado = peticiontempeada()
    listado.linkapi = url
    listado.stringjson = peticion.text
    if caducidad!=-1:
        listado.caducidad = caducidad
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
    url: str = "https://api.mangaupdates.com/v1/lists/0/search"
    if comprobar_si_toca_pedir(url):
        print("tabla ids leidos no encontrada")
        longitud: dict[str, int] = {"page": 1,
         "perpage": 1000}
        cont: str = json.dumps(longitud)
        peticion: requests.Response = hacer_peticion_post(url=url, cont=cont)
        if peticion.ok:
            cachear_peticion(peticion=peticion, url=url, caducidad=-1)
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

def iterador_cadena_json_listas() -> Iterator[str]:
    rellenar_tabla_ids_leidos_si_necesario()
    lista_filtrada: list[peticiontempeada]|None = devolver_lista_ocurrencias_por_linkapi(
        r"^https://api\.mangaupdates\.com/v1/lists/\d+/search$")
    #consigue bien la lista filtrada
    if lista_filtrada is None:
        print("no se encuentra tal ocurrencia") 
        print("fallo al construir la lista de ids ponderados m1")
        sys.exit(13)
    return lista_peticiones_a_iterator_de_propiedad(
        lista=lista_filtrada,
        propiedad="stringjson")


IdNamePeso: TypeAlias = tuple[int,str,float]
def iterador_tabla_ids_ponderados_m1() -> Iterator[IdNamePeso]:
    lista_filtrada_iterable:Iterator[str] = iterador_cadena_json_listas()
    for cadenajson in lista_filtrada_iterable:
        #print(f"cadenajson:\n\t{cadenajson}")
        diccionario_bucle = json.loads(cadenajson)["results"]
        for dict_serie in diccionario_bucle:
            rat = dict_serie["metadata"]["series"]["bayesian_rating"]
            rat = rat if isinstance(rat, Number) else 0.0
            assert isinstance(rat, Number)
            rating = float(cast(float, rat))
            id_serie: int = dict_serie["record"]["series"]["id"]
            leidos = dict_serie["record"]["status"]["chapter"]
            leidos = leidos if isinstance(leidos, Number) else 1
            totales = dict_serie["metadata"]["series"]["latest_chapter"]
            totales = totales if isinstance(totales, Number) else leidos
            totales = totales if not totales==0 else 1
            nombre = dict_serie["record"]["series"]["title"]
            assert isinstance(rating, float)
            assert isinstance(leidos, int)
            assert isinstance(totales, int)
            progreso: float = leidos / totales
            # print(f"añadiendo id {elid}")
            yield (id_serie, nombre, rating*progreso)

def rellenar_grupos_de_id_si_necesario(id_serie: int) -> None:
    url = f"https://api.mangaupdates.com/v1/series/{id_serie}/groups"
    if comprobar_si_toca_pedir(url):
        peticion = hacer_peticion_get(url=url)
        if peticion.ok:
            cachear_peticion(peticion=peticion, url=url)
        else:
            print("error petición series id")
            sys.exit(peticion.status_code)

def grupos_serie_por_id(id: int) -> set[tuple[int, str]]:
    rellenar_grupos_de_id_si_necesario(id_serie=id)
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

def ordenar_listatuplas(lista_tuplas: list[IdNamePeso]) -> list[IdNamePeso]:
    newlist = sorted(lista_tuplas, key=lambda x: x[2], reverse=True)
    return newlist

def tabla_GidNP_recomendados() -> list[IdNamePeso]:
    dict_total_grupos: dict[int, tuple[str, float]] = {}
    for tupla in iterador_tabla_ids_ponderados_m1():
        id_serie, nombre, puntos = tupla
        conjunto_parcial_grupos: set[tuple[int, str]] = grupos_serie_por_id(
            id=id_serie)
        for grupo_id, nombre_grupo in conjunto_parcial_grupos:
            if grupo_id in dict_total_grupos.keys():
                nombre, a_puntos = dict_total_grupos[grupo_id]
                dict_total_grupos[grupo_id] = (nombre, a_puntos+puntos)
            else:
                dict_total_grupos.setdefault(grupo_id, (nombre_grupo, puntos))
    lista_total_grupos: list[IdNamePeso] = []
    for grupo_id in dict_total_grupos.keys():
        nombre, peso = dict_total_grupos[grupo_id]
        tupla_a_sumar: IdNamePeso = (grupo_id, nombre, peso)
        lista_total_grupos.append(tupla_a_sumar)
    lista_total_grupos = ordenar_listatuplas(lista_total_grupos)
    return lista_total_grupos


def iterador_series_por_grupo(grupo_id:int) -> Iterator[IdNamePeso]:
    for tupla in iterador_tabla_ids_ponderados_m1():
        id_serie, nombre, puntos = tupla
        conjunto_parcial_grupos: set[tuple[int, str]] = grupos_serie_por_id(
            id=id_serie)
        for gid, _ in conjunto_parcial_grupos:
            if gid==grupo_id:
                yield (id_serie, nombre, puntos)


def iterador_top_grupos(f_grupos: Callable[..., list[IdNamePeso]], num:int) -> Iterator[IdNamePeso]:
    grupos_totales: list[tuple[int, str, float]] = f_grupos()
    for tupla in grupos_totales[:num]:
        yield tupla

def opcion_top_grupos(num:int) -> Iterator[tuple[str, ...]]:
    for id, nombre, peso in iterador_top_grupos(
        f_grupos=tabla_GidNP_recomendados,
        num=num):
        yield (str(id), nombre, str(peso))

def opcion_blame_grupo(gid:int) -> Iterator[tuple[str, ...]]:
    for id, nombre, peso in iterador_series_por_grupo(
        grupo_id=gid):
        yield (str(id), nombre, str(peso))

def escupir_tabla_IdNamePeso(
        it_tupla_imprimible: Iterator[tuple[str, ...]],
        titulo_tabla: str,
        tupla_de_columnas: tuple[str, ...]) -> None:
    tabla = Table(title=titulo_tabla)
    for columna in tupla_de_columnas:
        tabla.add_column(columna)
    for fila in it_tupla_imprimible:
        if len(tupla_de_columnas)==len(fila):
            tabla.add_row(*fila)
        else:
            print("Error: longitud de fila no corresponde a la de columna")
            print("Fila:")
            print(f"\t{fila}")
            print("Columnas:")
            print(f"\t{tupla_de_columnas}")
            sys.exit(19)
    console = Console()
    console.print(tabla)

def imprimir_opciones() -> None:
    print("Elegir de entre las opciones:")
    print("\t1. Imprimir grupos más recomendados")
    print("\t2. Analizar puntuación de un grupo")
    print("\t3. Analizar puntuacion")
    print("\n\t99. Salir")

def elegir_entre_opciones() -> None:
    imprimir_opciones()
    num_opcion:int = int(input("\nNúmero de Opción: "))
    match num_opcion:
        case 1:
            numero:int = int(input("Numero de Resultados: "))
            iterador: Iterator[tuple[str, ...]] = opcion_top_grupos(
                num=numero)
            escupir_tabla_IdNamePeso(
                it_tupla_imprimible=iterador,
                titulo_tabla="Grupos Recomendados",
                tupla_de_columnas=("Nombre", "Id", "Peso"))
        case 2:
            grupo_id:int = int(input("Id del grupo a analizar: "))
            iterador2:Iterator[tuple[str, ...]] = opcion_blame_grupo(
                gid=grupo_id)
            escupir_tabla_IdNamePeso(
                it_tupla_imprimible=iterador2,
                titulo_tabla="Series Causantes",
                tupla_de_columnas=("Nombre", "Id", "Peso"))
        case 99:
            print(despido)
            sys.exit(0)
        case _:
            elegir_entre_opciones()

if __name__ == "__main__":
    leer_peticiones()
    # tanto monta
    #print(peticiones)
    elegir_entre_opciones()
    # monta tanto
    # escribir_peticiones()
    sys.exit(0)
