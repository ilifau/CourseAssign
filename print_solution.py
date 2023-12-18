import csv


def print_and_write_solution(m, x, z, q, items, choices, instanceName, settings=None):
    output = [['obj_id', 'user_id', 'item_id']]
    # get courses from items
    courses = items.item_id.unique()
    obj_id = items.obj_id.tolist()[0]
    # get students from choices
    students = choices.user_id.unique()

    if str(type(settings)) == "<class 'NoneType'>":
        priority_depth = len(list(choices.priority.unique()))
        num_assignments = 1
    else:
        priority_depth = settings.num_priorities.tolist()[0]
        num_assignments = settings.num_assignments.tolist()[0]
    
    prioritised_counts = [0 for i in range(priority_depth)]
    assigned_count = 0
    for i in range(len(students)):
        for j in range(len(courses)):
            if i == 0:
                #print(z[j].x)
                pass
            if q[i][j] == 0:
                if x[(i,j)].x != 1.0 and x[(i,j)].x != 0.0:
                    #print(x[(i,j)].x)
                    pass
                dummy = choices.loc[choices['user_id'] == students[i]]
                dummy_2 = dummy.loc[dummy['item_id'] == courses[j]]
                if len(dummy_2.index) == 1:
                    students_choice = int(dummy_2.iloc[0]['priority'])

                    if x[(i, j)].x == 1:
                        prioritised_counts[students_choice] += 1
                        assigned_count += 1
                if x[(i, j)].x == 1:
                    output.append([obj_id, students[i], courses[j]])

    with open(instanceName + "/{}_solution.csv".format(instanceName), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(output)
