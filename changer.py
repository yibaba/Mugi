import time
import pickle


class idtable:
    def __init__(self):
        self.dic = {}
        self.timestamp = 0.0


losids = idtable()


if __name__ == "__main__":
    with open("losids", "rb") as losids_f:
        losids
        tlosids = pickle.load(losids_f)
        if tlosids != 0:
            print("Exito cargando ids")
            losids = tlosids
    losids.timestamp = time.time()
    print(losids.timestamp)
    with open("losids", "wb") as losids_f:
        pickle.dump(losids, losids_f)
