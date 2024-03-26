import pandas as pd

#Read input
inputData = pd.read_excel('data/data.xlsx')

#Recovery Names
nameById = inputData["Nome"].to_dict()
lastDay = 28 #TODO

#Sets
Crops = list(nameById.keys())
Areas = list(range(0,45))  #TODO
Days = list(range(1,lastDay+1)) 

#Parameters
ReapDays = inputData["Tempo"].to_dict()
Regrowth = inputData["Recorrência"].map(lambda x: x == "Sim").to_dict()
RegrowthDays = inputData["Tempo Recorrência"].to_dict() #float and string, need to cast later
Founds = 2000 #TODO
Price = inputData["Preço"].to_dict()
BaseSellPrice = inputData["Venda"].to_dict() 



def calcIsReap(RegrowthDays, Regrowth, ReapDays, Crops, Days):
    isReap = {}
    for c in Crops:
        isReap[c] = {}
        for dc in Days:
            isReap[c][dc] = {}
            for dr in Days:
                diffDays = dr - dc
                if diffDays <= 0 or diffDays < ReapDays[c]:
                    isReap[c][dc][dr] = 0
                elif diffDays == ReapDays[c]:
                    isReap[c][dc][dr] = 1
                else:
                    if Regrowth[c] and diffDays - ReapDays[c] % RegrowthDays[c] == 0:
                        isReap[c][dc][dr] = 1
                    else:
                       isReap[c][dc][dr] = 0
    return isReap
                
