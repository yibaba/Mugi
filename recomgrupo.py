import requests
#from rich.progress import track
from rich.console import Console
from rich.table import Table
import time
from numbers import Number
import json
import pickle
import sys
from typing import Any, Callable, Iterator, TypeAlias, TypeVar, cast
#import fnmatch
import re
from random import randint
import itertools

cooloff: float = 0.9

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
        self.caducidad: int = randint(1, 3)*((12*60*60)+randint(1, 120))

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
        print(caducidad/3600)
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
            cachear_peticion(peticion=peticion, url=url)
        else:
            print("error petición tabla ids")
            sys.exit(peticion.status_code)

def rellenar_serie_id_si_necesario(id: int) -> None:
    url: str = f"https://api.mangaupdates.com/v1/series/{id}"
    if comprobar_si_toca_pedir(url):
        print("serie id leidos no encontrado")
        peticion: requests.Response = hacer_peticion_get(url=url)
        if peticion.ok:
            caducidad: int = randint(1,7)*((24*60*60) + randint(0,3600))
            cachear_peticion(peticion=peticion, url=url, caducidad=caducidad)
        else:
            print("error petición serie id")
            print(url)
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

def iterador_cadenajson_de_series_leyendo() -> Iterator[str]:
    lista_ids_leyendas: Iterator[str] = iterador_cadena_json_listas()
    for cadenajson in lista_ids_leyendas:
        diccionario_bucle = json.loads(cadenajson)["results"]
        for dict_serie in diccionario_bucle:
            yield json.dumps(dict_serie)

def conseguir_cadena_json_capo(id: int) -> Iterator[str]:
    rellenar_serie_id_si_necesario(id=id)
    lista_capo: list[peticiontempeada]|None = devolver_lista_ocurrencias_por_linkapi(
        f"^https://api.mangaupdates.com/v1/series/{id}$")
    if lista_capo is None:
        print("no se encuentra tal ocurrencia")
        print("fallo al construir lista_capo")
        sys.exit(12)
    return lista_peticiones_a_iterator_de_propiedad(
        lista=lista_capo,
        propiedad="stringjson")

def conseguir_total_caps(id: int) -> int|None:
    capo_json: Iterator[str] = conseguir_cadena_json_capo(id)
    patron: str = r"^\d+$"
    r = re.compile(patron)
    dig = r"\d+"
    for cadenajson in capo_json:
        estatus: str|None = json.loads(cadenajson)["status"]
        if estatus is None:
            l_num = []
        else:
            lista_json: list[str] = re.findall(dig, estatus)
            l_cad_num: list[str] = list(filter(lambda x: r.match(x), lista_json))
            l_num: list[int] = list(map(lambda x: int(x), l_cad_num))
        if not l_num:
            return None
        else:
            return max(l_num)

IdNaRatLedTot: TypeAlias = tuple[int, str, float, int, int]
def cadenajson_lista_a_tabla_IdNaRatLedTot(cadenajson:str) -> IdNaRatLedTot:
    dict_serie = json.loads(cadenajson)
    rat = dict_serie["metadata"]["series"]["bayesian_rating"]
    rat = rat if isinstance(rat, Number) else 0.0
    assert isinstance(rat, Number)
    rating = float(cast(float, rat))
    id_serie: int = dict_serie["record"]["series"]["id"]
    leidos = dict_serie["record"]["status"]["chapter"]
    leidos = leidos if isinstance(leidos, Number) else 1
    # totales = dict_serie["metadata"]["series"]["latest_chapter"]
    # totales = totales if isinstance(totales, Number) else leidos
    # totales = totales if not totales==0 else 1
    totales: int|None = conseguir_total_caps(id=id_serie)
    if totales is None:
        totales = dict_serie["metadata"]["series"]["latest_chapter"]
        totales = totales if isinstance(totales, Number) else cast(int, leidos)
        totales = totales if not totales==0 else 1
    if cast(int, leidos)>cast(int, totales):
        totales = 1
        leidos = 1
    nombre = dict_serie["record"]["series"]["title"]
    assert isinstance(rating, float)
    assert isinstance(leidos, int)
    assert isinstance(totales, int)
    return (id_serie, nombre, rating, leidos, totales)

def iterador_tabla_IdNaRatLedTot() -> Iterator[IdNaRatLedTot]:
    for cadenajson in iterador_cadenajson_de_series_leyendo():
        yield cadenajson_lista_a_tabla_IdNaRatLedTot(cadenajson=cadenajson)

def fn_id_a_link(id: int) -> str:
    resultado: str = ""
    dict_serie = conseguir_cadena_json_capo(id=id)
    for cadjson in dict_serie:
        resultado = json.loads(cadjson)["url"]
    return resultado

def cadenajson_serie_a_tabla_IdNaRatLedTot(cadenajson:str) -> IdNaRatLedTot:
    dict_serie = json.loads(cadenajson)
    id_serie: int = dict_serie["series_id"]
    for id, na, rat, led, tot in iterador_tabla_IdNaRatLedTot():
        if id==id_serie:
            return (id, na, rat, led, tot)
    return (0, "0", 6, 1, 1)

IdNamePeso: TypeAlias = tuple[int,str,float]
def iterador_sid_a_catrecsyrecs_IdNaWh(sid:int) -> Iterator[IdNamePeso]:
    cadjsonserie = conseguir_cadena_json_capo(sid)
    for cadenajson in cadjsonserie:
        dict_serie = json.loads(cadenajson)
        ckid, _, rat,led, tot = cadenajson_serie_a_tabla_IdNaRatLedTot(cadenajson)
        if ckid==0:
            print("error cadenajson de serie estaba en la lista")
            sys.exit(58)
        prepeso = rat*(led / tot)
        rectab = dict_serie["recommendations"]
        catrectab = dict_serie["category_recommendations"]
        if rectab:
            for dict_recs in rectab:
                if dict_recs:
                    peso = prepeso * dict_recs["weight"]
                    yield (dict_recs["series_id"], 
                           dict_recs["series_name"], 
                           peso)
        if catrectab:
            for dict_recs in catrectab:
                if dict_recs:
                    peso = prepeso * dict_recs["weight"]
                    yield (dict_recs["series_id"], 
                           dict_recs["series_name"], 
                           peso)

def cadenajson_serie_a_IdNamePeso(cadenajson: str) -> IdNamePeso:
    dict_serie = json.loads(cadenajson)
    sid = dict_serie["series_id"]
    nombre = dict_serie["title"]
    prepeso: float|None = dict_serie["bayesian_rating"]
    peso: float = 0.0
    if prepeso is not None:
        peso = prepeso
    return (sid, nombre, peso)

def iterador_tabla_recs_nat_IdNaP():
    conjunto_leyendo: set[int] = set()
    for cadenajson in iterador_cadenajson_de_series_leyendo():
        dict_serie_lista = json.loads(cadenajson)
        conjunto_leyendo.add(
            dict_serie_lista["record"]["series"]["id"])
    for sid in conjunto_leyendo:
        for id_recseries, nombre, peso in iterador_sid_a_catrecsyrecs_IdNaWh(
            sid=sid):
            if not (id_recseries in conjunto_leyendo):
                yield (id_recseries, nombre, peso)

def iterador_tabla_IdNamePeso() -> Iterator[IdNamePeso]:
    for id, na, rat, led, tot in iterador_tabla_IdNaRatLedTot():
        prog = led / tot
        yield (id, na, rat*prog)

def rellenar_grupos_de_id_si_necesario(id_serie: int) -> None:
    url = f"https://api.mangaupdates.com/v1/series/{id_serie}/groups"
    if comprobar_si_toca_pedir(url):
        peticion = hacer_peticion_get(url=url)
        if peticion.ok:
            caducidad: int = randint(1,7)*((24*60*60) + randint(0,3600))
            cachear_peticion(peticion=peticion, url=url, caducidad=caducidad)
        else:
            print("error petición grupo series id")
            sys.exit(peticion.status_code)

def rellenar_series_de_grupo_de_id_si_necesario(gid: int) -> None:
    url = f"https://api.mangaupdates.com/v1/groups/{gid}/series"
    if comprobar_si_toca_pedir(url):
        peticion = hacer_peticion_get(url=url)
        if peticion.ok:
            cachear_peticion(peticion=peticion, url=url)
        else:
            print("error petición grupo id")
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

def series_grupo_por_id(gid: int) -> Iterator[IdNamePeso]:
    rellenar_series_de_grupo_de_id_si_necesario(gid=gid)
    lista_recomendados: list[peticiontempeada]|None = devolver_lista_ocurrencias_por_linkapi(
        f"^https://api.mangaupdates.com/v1/groups/{gid}/series$")
    if lista_recomendados is None:
        print("no se encuentra tal ocurrencia")
        print("fallo al construir lista_recomendados")
        sys.exit(12)
    lista_recomendados_iterable: Iterator[str] = lista_peticiones_a_iterator_de_propiedad(
        lista=lista_recomendados,
        propiedad="stringjson")
    series_uniq: set[tuple[int, str]] = set()
    for cadenajson in lista_recomendados_iterable:
        diccionario_bucle = json.loads(cadenajson)["series_titles"]
        for dict_series in diccionario_bucle:
            id = dict_series["series_id"]
            nom = dict_series["title"]
            if id is not None:
                series_uniq.add((id, nom))
            else:
                print(f"Nombre {nom}")
    for sid, nombre in series_uniq:
        cadjsonserie = conseguir_cadena_json_capo(id=sid)
        for cadenajson in cadjsonserie:
            _, _, peso = cadenajson_serie_a_IdNamePeso(cadenajson=cadenajson)
            yield (sid, nombre, peso)

def series_grupo_por_id_ordenadas(gid: int) -> list[IdNamePeso]:
    lista_series: list[IdNamePeso] = []
    for id, nom, wht in series_grupo_por_id(
        gid=gid):
        lista_series.append((id, nom, wht))
    return ordenar_listatuplas(lista_series)

def tabla_GidNP_recomendados() -> list[IdNamePeso]:
    dict_total_grupos: dict[int, tuple[str, float]] = {}
    for tupla in iterador_tabla_IdNamePeso():
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

def conseguir_serie_grupo(gid: int, cuenta: int) -> tuple[int, str]:
    lista_series: list[IdNamePeso] = series_grupo_por_id_ordenadas(gid=gid)
    if len(lista_series)>cuenta:
        id, nom, _= lista_series[cuenta]
        return (id, nom)
    else:
        return (0, "")

def iterador_series_por_grupo(grupo_id:int) -> Iterator[IdNamePeso]:
    for tupla in iterador_tabla_IdNamePeso():
        id_serie, nombre, puntos = tupla
        conjunto_parcial_grupos: set[tuple[int, str]] = grupos_serie_por_id(
            id=id_serie)
        for gid, _ in conjunto_parcial_grupos:
            if gid==grupo_id:
                yield (id_serie, nombre, puntos)

def iterador_top_grupos(f_grupos: Callable[..., list[IdNamePeso]], num:int) -> Iterator[IdNamePeso]:
    grupos_totales: list[IdNamePeso] = f_grupos()
    for tupla in grupos_totales[:num]:
        yield tupla

def iterador_recs_nativo() -> Iterator[IdNamePeso]:
    dict_respuesta: dict[int, tuple[str, float]] = {}
    for id, nom, wht in iterador_tabla_recs_nat_IdNaP():
        if id in dict_respuesta.keys():
            nombre, a_peso = dict_respuesta[id]
            dict_respuesta[id] = (nombre, a_peso+wht)
        else:
            dict_respuesta.setdefault(id, (nom, wht))
    for sid in dict_respuesta.keys():
        nombre, peso = dict_respuesta[sid]
        yield (sid, nombre, peso)

# Churro, función fea y muy grande
def iterador_recs_basado_gr(num: int) -> Iterator[tuple[int, str, str, float]]:
    bucleando: bool = True
    grupos_totales: list[IdNamePeso] = tabla_GidNP_recomendados()
    tabla_tenidos: list[int] = []
    total_puntos: float = 0.0
    for _, _, wht in grupos_totales:
        total_puntos += wht
    resta: float = total_puntos / num
    for id, _, _, _, _ in iterador_tabla_IdNaRatLedTot():
        tabla_tenidos.append(id)
    cuenta: dict[int, int] ={}
    printejo = 0
    while bucleando:
        id, nom, wht = grupos_totales[0]
        print(f"{nom}, {wht}")
        if wht>0:
            if id in cuenta.keys():
                cuenta[id] += 1
            else:
                cuenta.setdefault(id, 0)
            nuevo_peso = wht - resta
            grupos_totales.append((id, nom, nuevo_peso))
            del grupos_totales[0]
            grupos_totales = ordenar_listatuplas(grupos_totales)
            sid, na = conseguir_serie_grupo(gid=id, cuenta=cuenta[id])
            while (sid in tabla_tenidos) and (sid!=0):
                cuenta[id] +=1
                sid, na = conseguir_serie_grupo(gid=id, cuenta=cuenta[id])
            if sid!=0:
                printejo += 1
                print(printejo)
                tabla_tenidos.append(sid)
                yield (sid, na, nom, wht)
        else:
            bucleando = False

def iterador_CatPeso() -> Iterator[tuple[str, float]]:
    for id, _, wht in iterador_tabla_IdNamePeso():
        cadenajson = conseguir_cadena_json_capo(id=id)
        for cadjson in cadenajson:
            dict_serie = json.loads(cadjson)
            for dict_cats in dict_serie["categories"]:
                cat: str = dict_cats["category"]
                votos: int = dict_cats["votes"]
                yield (cat, votos*wht)

def iterador_GenrPeso() -> Iterator[tuple[str, float]]:
    for id, _, wht in iterador_tabla_IdNamePeso():
        cadenajson = conseguir_cadena_json_capo(id=id)
        for cadjson in cadenajson:
            dict_serie = json.loads(cadjson)
            for dict_genr in dict_serie["genres"]:
                yield (dict_genr["genre"], wht)

def tabla_CatPeso() -> list[tuple[str, float]]:
    dict_cats: dict[str, float] = {}
    for cat, wht in iterador_CatPeso():
        if cat in dict_cats.keys():
            dict_cats[cat] += wht
        else:
            dict_cats.setdefault(cat, wht)
    lista_total: list[tuple[str, float]] = []
    for cat in dict_cats.keys():
        lista_total.append((cat, dict_cats[cat]))
    return lista_total

def tabla_GenrPeso() -> list[tuple[str, float]]:
    dict_genr: dict[str, float] = {}
    for genr, wht in iterador_GenrPeso():
        if genr in dict_genr.keys():
            dict_genr[genr] += wht
        else:
            dict_genr.setdefault(genr, wht)
    lista_total: list[tuple[str, float]] = []
    for genr in dict_genr.keys():
        lista_total.append((genr, dict_genr[genr]))
    return lista_total

def iterador_cats_orden() -> Iterator[tuple[str, float]]:
    lista_ordenable: list[IdNamePeso] = []
    for cat, wht in tabla_CatPeso():
        lista_ordenable.append((0, cat, wht))
    for genr, wht in tabla_GenrPeso():
        lista_ordenable.append((0, genr, wht))
    lista_ordenable = ordenar_listatuplas(lista_ordenable)
    for _, categoria, peso in lista_ordenable:
        yield (categoria, peso)

ItTFilas: TypeAlias = Iterator[tuple[str, ...]]
def opcion_top_grupos(num: int) -> ItTFilas:
    for id, nombre, peso in iterador_top_grupos(
        f_grupos=tabla_GidNP_recomendados,
        num=num):
        yield (str(id), nombre, str(peso))

def opcion_blame_grupo(gid: int) -> ItTFilas:
    for id, nombre, peso in iterador_series_por_grupo(
        grupo_id=gid):
        yield (str(id), nombre, str(peso))

def opcion_analiza_serie(sid: int) ->ItTFilas:
    for id, nom, rat, led, tot in iterador_tabla_IdNaRatLedTot():
        if sid==id:
            rating: str = str(rat)
            leidos: str = str(led)
            total: str = str(tot)
            yield (nom, rating, leidos, total)

def opcion_recs_clasico(num: int) -> ItTFilas:
    for id, nombre, wght in itertools.islice(
        iterador_recs_nativo(), num):
        sid: str = str(id)
        peso: str = str(wght)
        yield (sid, nombre, peso)

def opcion_id_a_url(id: int) -> ItTFilas:
    url_resultado: str = ""
    rid: str = str(id)
    for caracter in fn_id_a_link(id):
        url_resultado += caracter
    yield (rid, url_resultado)

def opcion_recs_grupo(num: int) -> ItTFilas:
    for id, nombre, nombre_grupo, wht in itertools.islice(
        iterador_recs_basado_gr(num), num):
        sid: str = str(id)
        peso: str = str(wht)
        yield (sid, nombre, nombre_grupo, peso)

def opcion_top_cats(num: int) -> ItTFilas:
    for nom, wht in itertools.islice(
        iterador_cats_orden(), 
        num):
        peso: str = str(wht)
        yield(nom, peso)

def escupir_tabla_ItTFilas(
        it_tupla_imprimible: ItTFilas,
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
    print("\t4. Recomendador versión clásica")
    print("\t5. Id de serie a enlace")
    print("\t6. Recomendador versión grupos")
    print("\t7. Imprimir categorías más usadas")
    print("\n\t99. Salir")

def elegir_entre_opciones() -> None:
    imprimir_opciones()
    num_opcion:int = int(input("\nNúmero de Opción: "))
    match num_opcion:
        case 1:
            numero: int = int(input("Numero de Resultados: "))
            iterador: ItTFilas = opcion_top_grupos(
                num=numero)
            escupir_tabla_ItTFilas(
                it_tupla_imprimible=iterador,
                titulo_tabla="Grupos Recomendados",
                tupla_de_columnas=("Nombre", "Id", "Peso"))
        case 2:
            grupo_id: int = int(input("Id del grupo a analizar: "))
            iterador2: Iterator[tuple[str, ...]] = opcion_blame_grupo(
                gid=grupo_id)
            escupir_tabla_ItTFilas(
                it_tupla_imprimible=iterador2,
                titulo_tabla="Series Causantes",
                tupla_de_columnas=("Id", "Nombre", "Peso"))
        case 3:
            id_serie:int = int(input("\nId de la serie a analizar: "))
            iterador3: ItTFilas = opcion_analiza_serie(sid=id_serie)
            escupir_tabla_ItTFilas(
                it_tupla_imprimible=iterador3,
                titulo_tabla="Desglose Series",
                tupla_de_columnas=("Nombre", "Puntuación", "Leidos", "Total"))
        case 4:
            numero: int = int(input("Número de recomendaciones:"))
            iterador4: ItTFilas = opcion_recs_clasico(num=numero)
            escupir_tabla_ItTFilas(
                it_tupla_imprimible=iterador4, 
                titulo_tabla="Series Recomendadas", 
                tupla_de_columnas=("Id", "Nombre", "Peso"))
        case 5:
            id_entrada: int = int(input("Id de serie: "))
            iterador5: ItTFilas = opcion_id_a_url(id=id_entrada)
            escupir_tabla_ItTFilas(
                it_tupla_imprimible=iterador5, 
                titulo_tabla="Resultado", 
                tupla_de_columnas=("Id", "Url"))
        case 6:
            numero: int = int(input("Número de recomendaciones: "))
            iterador6: ItTFilas = opcion_recs_grupo(num=numero)
            escupir_tabla_ItTFilas(
                it_tupla_imprimible=iterador6, 
                titulo_tabla="Series Recomendadas (G)", 
                tupla_de_columnas=("Id", "Nombre", "Grupo", "Peso"))
        case 7:
            numero: int = int(input("Número de categorías: "))
            iterador7: ItTFilas = opcion_top_cats(num=numero)
            escupir_tabla_ItTFilas(
                it_tupla_imprimible=iterador7, 
                titulo_tabla="Categorías en Uso", 
                tupla_de_columnas=("Nombre", "Peso"))
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
    escribir_peticiones()
    sys.exit(0)
