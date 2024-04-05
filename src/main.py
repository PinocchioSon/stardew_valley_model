import math
import pandas as pd
from ortools.linear_solver import pywraplp

def calcIsReap(RegrowthDays, Regrowth, ReapDays, Crops, Days):
    isReap = {}
    for c in Crops:
        isReap[c] = {}
        for dc in Days:
            isReap[c][dc] = {}
            for dr in Days:
                diffDays = dr - dc
                if diffDays <= 0 or diffDays < ReapDays[c]:
                    isReap[c][dc][dr] = False
                elif diffDays == ReapDays[c]:
                    isReap[c][dc][dr] = True
                else:
                    if Regrowth[c] and (diffDays - ReapDays[c]) % RegrowthDays[c] == 0:
                        isReap[c][dc][dr] = True
                    else:
                        isReap[c][dc][dr] = False
    return isReap

def calcIsGrowing(Regrowth, ReapDays, Crops, Days):
    IsGrowing = {}
    for c in Crops:
        IsGrowing[c] = {}
        for dc in Days:
            IsGrowing[c][dc] = {}
            for dr in Days:
                diffDays = dr - dc
                IsGrowing[c][dc][dr] = diffDays < ReapDays[c] or Regrowth[c]
    return IsGrowing

def calcPricePerDay(Crops, Days, Price, JojaPrice, SpecialPrice, SpecialDays, Season):
    PricePerDay = {}
    CanBeBough = {}
    for crop in Crops:
        PricePerDay[crop] = {}
        CanBeBough[crop] = {}
        if math.isnan(Price[crop]):
            for day in Days:
                PricePerDay[crop][day] = 0
                CanBeBough[crop][day] = False
            PricePerDay[crop][SpecialDays[crop]] = SpecialPrice[crop]
            CanBeBough[crop][SpecialDays[crop]] = True
            continue
        for day in Days:
            CanBeBough[crop][day] = True
            if Season == "Primavera" and day == 13:
                CanBeBough[crop][day] = False
            if day % 7 == 3: # Pierre closed
               PricePerDay[crop][day] =  JojaPrice[crop]
            else:
                PricePerDay[crop][day] =  Price[crop]
    return PricePerDay, CanBeBough
            

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
Founds = 500 #TODO
Price = inputData["Preço"].to_dict()
JojaPrice = inputData["Preço Joja"].to_dict()
SpecialPrice = inputData["Preço Especial"].to_dict()
BaseSellPrice = inputData["Venda"].to_dict() 
SpecialDays = inputData["Dias Especiais"].to_dict()
FixedCrops = inputData["Fixo"].to_dict()
FirstDay = Days[0]
IsReap = calcIsReap(RegrowthDays, Regrowth, ReapDays, Crops, Days)
IsGrowing = calcIsGrowing(Regrowth, ReapDays, Crops, Days)
PricePerDay, CanBeBough = calcPricePerDay(Crops, Days, Price, JojaPrice, SpecialPrice, SpecialDays, "Primavera")

#Increment founds to attend fixed start Crops
Founds += sum([PricePerDay[x][FirstDay] * FixedCrops[x] for x in Crops])


solver = pywraplp.Solver.CreateSolver("SCIP")

y_vars = {}
for c in Crops:
    y_vars[c] = {}
    for a in Areas:
        y_vars[c][a] = {}
        for d in Days:
            if CanBeBough[c][d]:
                y_vars[c][a][d] = solver.IntVar(0,1,str('y_'+str(c)+'_'+str(a)+'_'+str(d)))
            else:
                y_vars[c][a][d] = solver.IntVar(0,0,str('y_'+str(c)+'_'+str(a)+'_'+str(d)))

cash = {}
for d in Days:
    cash[d] = solver.IntVar(lb=0, ub=Founds*100, name='d_'+str(d))


objective = solver.Objective()
objective.SetCoefficient(cash[lastDay], 1)
objective.SetMaximization()

for d in Days:
    ct = solver.Constraint("gold_per_d"+str(d))
    if d == FirstDay:
        ct.SetLb(-Founds)
    else:
        ct.SetLb(0)
        ct.SetCoefficient(cash[d-1], 1)
    ct.SetCoefficient(cash[d], -1)
    for c in Crops:
        for a in Areas:
            ct.SetCoefficient(y_vars[c][a][d], -Price[c])
            for dc in Days:
                if IsReap[c][dc][d]:
                    ct.SetCoefficient(y_vars[c][a][dc], BaseSellPrice[c])

    for a in Areas:
        cta = solver.Constraint("one_crop_a"+ str(a)+"d"+str(d))
        cta.SetUb(1)
        for c in Crops:
            for dc in Days:
                if IsGrowing[c][dc][d]:
                    cta.SetCoefficient(y_vars[c][a][dc], 1)
solver.EnableOutput()
solver.Solve()



for c in Crops:
    for a in Areas:
        for d in Days:
            if y_vars[c][a][d].solution_value() > 0:
                print(y_vars[c][a][d].solution_value())
for d in Days:
    print(cash[d].solution_value())

lp = solver.ExportModelAsLpFormat(False)

with open("lp.lp", "w") as text_file:
    text_file.write(lp)

output = {}
output['gold'] = {}
for c in Crops:
    output[nameById[c]] = {}
    for d in Days:
        output['gold'][d] = cash[d].solution_value()
        output[nameById[c]][d] = 0
        for a in Areas:
            if y_vars[c][a][d].solution_value() > 0:
                 output[nameById[c]][d] += 1

df_output = pd.DataFrame.from_dict(output)