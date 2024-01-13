import requests
from rich.progress import track
from rich.console import Console
from rich.table import Table
import time
import numbers
import json
import pickle
import sys
tCadRecs = 60*60
thrTime = 0.3
credentials = {}

# obtener credenciales


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
