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
                    if Regrowth[c] and diffDays - ReapDays[c] % RegrowthDays[c] == 0:
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
                #if diffDays < ReapDays[c] or Regrowth[c]:
                #    IsGrowing[c][dc][dr] = 1
                #else:
                #    IsGrowing[c][dc][dr] = 0
    return IsGrowing

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
FirstDay = Days[0]
IsReap = calcIsReap(RegrowthDays, Regrowth, ReapDays, Crops, Days)
IsGrowing = calcIsGrowing(Regrowth, ReapDays, Crops, Days)


solver = pywraplp.Solver.CreateSolver("SCIP")

y_vars = {}
for c in Crops:
    y_vars[c] = {}
    for a in Areas:
        y_vars[c][a] = {}
        for d in Days:
            y_vars[c][a][d] = solver.NumVar(0,1,str('y_'+str(c)+'_'+str(a)+'_'+str(d)))

cash = {}
for d in Days:
    cash[d] = solver.NumVar(lb=0, ub=Founds*100, name='d_'+str(d))


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
                    ct.SetCoefficient(y_vars[c][a][d], BaseSellPrice[c])

    for a in Areas:
        cta = solver.Constraint("one_crop_a"+ str(a)+"d"+str(d))
        cta.SetUb(1)
        for c in Crops:
            for dc in Days:
                if IsGrowing[c][dc][d]:
                    cta.SetCoefficient(y_vars[c][a][d], 1)
solver.Solve()



for c in Crops:
    for a in Areas:
        for d in Days:
            if y_vars[c][a][d].solution_value() > 0:
                print(y_vars[c][a][d].solution_value())
for d in Days:
    print(cash[d].solution_value())
    