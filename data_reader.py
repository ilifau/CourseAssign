import pandas as pd
import os

def read_data(instanceName):
    items = pd.read_csv(instanceName + "/items.csv", sep=";")
    choices = pd.read_csv(instanceName + "/choices.csv", sep=";")

    if os.path.exists(instanceName + "/settings.csv"):
        settings = pd.read_csv(instanceName + "/settings.csv", sep=";")
    else:
        settings = None

    if os.path.exists(instanceName + "/conflicts.csv"):
        conflicts = pd.read_csv(instanceName + "/conflicts.csv", sep=";")
    else:
        conflicts = None
        
    if os.path.exists(instanceName + "/categories.csv"):
        categories = pd.read_csv(instanceName + "/categories.csv", sep=";")
    else:
        categories = None

    

    return items, choices, settings, conflicts, categories