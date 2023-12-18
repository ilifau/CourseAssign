from mip import *


def create_model(items, choices, settings=None, conflicts=None, categories=None, hard_constraint=True):

    # get courses from items
    courses = items.item_id.tolist()
    
    # sub_min, sub_max, obj_id from items
    sub_min = items.sub_min.tolist()
    sub_max = items.sub_max.tolist()

    # get students from choices
    students = choices.user_id.unique()

    # get category specifics
    if str(type(categories)) == "<class 'NoneType'>":
        cat_ids = categories.cat_id.tolist()
        cat_max = categories.max_assignments.tolist()
        course_cat = items.cat_id.tolist()

    # get priorities and number of assignments from settings
    if str(type(settings)) == "<class 'NoneType'>":
        priority_depth = len(list(choices.priority.unique()))
        num_assignments = 1
    else:
        priority_depth = settings.num_priorities.tolist()[0]
        num_assignments = settings.num_assignments.tolist()[0]

    # create cost coefficients based on number of courses, priorities and maximal sub_max
    coeff_base = float(len(courses))*float(len(students)) # theoretical base multiplier to avoid interference between priorities in the objective
    alt_coeff_base = 1<<(int(coeff_base)-1).bit_length() # next power of two for suggested numerical advantages for coefficients
    old_coeff_base = 1000 # previous versions coefficient multiplier

    coeff_choice = coeff_base

    coeff_list = [coeff_choice**(i) for i in range(priority_depth)]
    coeff_list.reverse()
    
    

    #create parameters
    c = [[[0 for j in range(len(items.index))] for k in range(priority_depth)] for i in
         range(len(students))]  # creates a multidimensional list with only zeros | [student][priority][course]
    q = [[1 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only ones

    '''d = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros
    e = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros'''

    if str(type(conflicts)) == "<class 'NoneType'>":
        conf = [[0 for j in range(len(items.index))] for i in range(len(items.index))]  # creates a multidimensional list with only zeros
        numb_conf = 0
        conflict_tuples = []
        for index, row in conflicts.iterrows():
            conflict_tuples.append([row['item1_id'], row['item2_id']])  # or row['item2_id'] == c1 and row['item1_id'] == c2:
            numb_conf += 1

        for l, c1 in enumerate(courses):
            for s, c2 in enumerate(courses):
                for tup in conflict_tuples:
                    if (tup[0] == c1) and (tup[1] == c2):# or row['item2_id'] == c1 and row['item1_id'] == c2:
                        conf[l][s] = 1
        print('numb_conf', numb_conf)
        #print(conf)

    for s, student in enumerate(students):
        student_choices = choices.loc[choices['user_id'] == student]

        for k, course in enumerate(courses):
            choice = student_choices.loc[student_choices['item_id'] == course]

            if len(choice.index) == 1:
                choice_priority = int(choice.priority.tolist()[0])
                c[s][choice_priority][k] = 1
                q[s][k] += - c[s][choice_priority][k]

            '''preferred = choice.loc[choice['priority'] == 1]
            if len(preferred.index) == 1:
                d[s][k] = 1
            super_preferred = choice.loc[choice['priority'] == 2]
            if len(super_preferred.index) == 2:
                e[s][k] = 1'''



    # create Gurobi model
    m = Model("student_assignment", solver_name=CBC)
    # create variables x, x_ij=1 if student i is assigned to course j
    x = {}
    for i in range(len(students)):
        for j in range(len(courses)):
            if hard_constraint: # model doesn't allow students to be left out
                if q[i][j] == 1:
                    x[(i, j)] = 0
                else: # model allows unequal assigning
                    x[(i, j)] = m.add_var(var_type=BINARY, name='x_{}_{}'.format(i, j))
            else:
                x[(i, j)] = m.add_var(var_type=BINARY, name='x_{}_{}'.format(i, j))
    # create variables z_j:
    # z_j is 0, if the number of students in course j is greater than or equal to the given minimum number s
    z = {}
    for j in range(len(courses)):
        z[j] = m.add_var(var_type=BINARY, name="z_{}_{}".format(i, j))

    # set objective function
    if hard_constraint:
        m.objective = maximize(xsum(xsum(coeff_choice*coeff_list[-1] * c[i][priority_depth-1][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))) +
                        coeff_list[-1] * xsum(z[j] for j in range(len(courses))) +
                        xsum(xsum(xsum(coeff_list[p] * c[i][p][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))) \
                            for p in range(priority_depth-1)))
    else:
        m.objective = maximize(xsum(xsum(coeff_choice*coeff_list[-1] * c[i][priority_depth-1][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))) +
                        coeff_list[-1] * xsum(z[j] for j in range(len(courses))) +
                        xsum(xsum(xsum(coeff_list[p] * c[i][p][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))) \
                            for p in range(priority_depth-1)) +
                        xsum(xsum((coeff_choice**2)*coeff_list[-1] * (-1) * q[i][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))))
    
    # ensures that the number of students in one course is less than or equal to the maximum number of participants
    for j in range(len(courses)):
        m.add_constr((xsum(x[(i, j)] for i in range(len(students))) <= sub_max[j] * (1 - z[j])), name="course_maximum_{}".format(j))

    # ensures that the number of students in one course is greater than or equal to the minimum number of participants
    for j in range(len(courses)):
        m.add_constr((sub_min[j] * (1 - z[j]) <= xsum(x[(i, j)] for i in range(len(students)))), name="course_minimum_{}".format(j))

    # ensures that each student is assigned the correct number of courses (default = 1)
    for i in range(len(students)):
        m.add_constr((xsum(x[(i, j)] for j in range(len(courses))) == num_assignments), name="num_assignments_{}".format(i))

    # ensures that each student can only be assigned to at most one course in a category
    if str(type(categories)) == "<class 'NoneType'>":
        for i in range(len(students)):
            LHS_student = 0
            for g, category in enumerate(cat_ids):
                LHS_category = 0
                coun = 0
                for j in range(len(courses)):
                    if course_cat[j] == category:
                        LHS_student += x[(i, j)]
                        LHS_category += x[(i, j)]
                        coun += 1
                m.add_constr(LHS_category <= cat_max[g])

    # ensures that at most one of two conflicting courses will be appointed to a student
    if str(type(conflicts)) == "<class 'NoneType'>":
        for i in range(len(students)):
            for l, c1 in enumerate(courses):
                for s, c2 in enumerate(courses):
                    if conf[l][s] == 1:
                        m.add_constr((x[(i, l)] + x[(i, s)] <= 1), name="conf{}_{}_{}".format(i, l, s))

    return m, x, z, q


###################################################################################################################################


def create_model_no_conflicts(items, choices):
    # get courses from items
    courses = items.item_id.tolist()
    # sub_min, sub_max, obj_id from items
    sub_min = items.sub_min.tolist()
    sub_max = items.sub_max.tolist()
    # get students from choices
    students = choices.user_id.unique()
    #create parameters
    c = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros
    q = [[1 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only ones
    d = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros
    e = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros
    count_p0 = 0
    count_p1 = 0
    count_p2 = 0
    for s, student in enumerate(students):
        student_choices = choices.loc[choices['user_id'] == student]
        for k, course in enumerate(courses):
            choice = student_choices.loc[student_choices['item_id'] == course]
            if len(choice.index) == 1:
                count_p0 += 1
                c[s][k] = 1
                q[s][k] += - c[s][k]
            preferred = choice.loc[choice['priority'] == 1]
            if len(preferred.index) == 1:
                count_p0 -= 1
                count_p1 += 1
                e[s][k] = 1
            super_preferred = choice.loc[choice['priority'] == 2]
            if len(super_preferred.index) == 1:
                d[s][k] = 1
                count_p0 -= 1
                count_p2 += 1
    print('count_p0', count_p0)
    print('count_p1', count_p1)
    print('count_p2', count_p2)


    # create Gurobi model
    m = Model("student_assignment", solver_name=CBC)
    # create variables x, x_ij=1 if student i is assigned to course j
    x = {}
    for i in range(len(students)):
        for j in range(len(courses)):
            if c[i][j] == 0:
                x[(i, j)] = 0
            else:
                x[(i, j)] = m.add_var(var_type=BINARY, name='x_{}_{}'.format(i, j))
    # create variables z_j:
    # z_j is 0, if the number of students in course j is greater than or equal to the given minimum number s
    z = {}
    for j in range(len(courses)):
        z[j] = m.add_var(var_type=BINARY, name="z_{}_{}".format(i, j))

    # set objective function:
    m.objective = maximize(xsum(xsum(10000 * c[i][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))) +
         100 * xsum(z[j] for j in range(len(courses))) +
         1 * (xsum(xsum(d[i][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses)))) +
         0.001 * (xsum(xsum(e[i][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses)))))

    # ensures that the number of students in one course is less than or equal to the maximum number of participants
    for j in range(len(courses)):
        m.add_constr((xsum(x[(i, j)] for i in range(len(students))) <= sub_max[j] * (1 - z[j])), name="course_maximum_{}".format(j))

    # ensures that the number of students in one course is greater than or equal to the minimum number of participants
    for j in range(len(courses)):
        m.add_constr((sub_min[j] * (1 - z[j]) <= xsum(x[(i, j)] for i in range(len(students)))), name="course_minimum_{}".format(j))

    # each student can only be assigned to at most one course in a category
    #for i in range(len(students)):
     #   m.addConstr(xsum(x[(i, j)] for j in range(len(courses))) <= 1)
    for i in range(len(students)):
        m.add_constr((xsum(x[(i, j)] for j in range(len(courses))) <= 1), name="at_most_one_student_{}".format(i))

    return m, x, z, q


def old(items, choices):
    # get courses from items
    courses = items.item_id.unique()
    # sub_min, sub_max, obj_id from items
    sub_min = items.sub_min.tolist()
    sub_max = items.sub_max.tolist()
    # get students from choices
    students = choices.user_id.unique()

    #create parameters
    c = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros
    q = [[1 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only ones
    d = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros
    e = [[0 for j in range(len(items.index))] for i in
         range(len(students))]  # creates a multidimensional list with only zeros

    for s, student in enumerate(students):
        student_choices = choices.loc[choices['user_id'] == student]
        for k, course in enumerate(courses):
            choice = student_choices.loc[student_choices['item_id'] == course]
            if len(choice.index) == 1:
                c[s][k] = 1
                q[s][k] += - c[s][k]
            preferred = choice.loc[choice['priority'] == 1]
            if len(preferred.index) == 1:
                d[s][k] = 1
            super_preferred = choice.loc[choice['priority'] == 2]
            if len(super_preferred.index) == 2:
                e[s][k] = 1

    # create Gurobi model
    m = Model("student_assignment", solver_name=CBC)
    # create variables x, x_ij=1 if student i is assigned to course j
    x = {}
    for i in range(len(students)):
        for j in range(len(courses)):
            x[(i, j)] = m.add_var(var_type=CONTINUOUS, ub=1, name='x_{}_{}'.format(i, j))
    # create variables z_j:
    # z_j is 0, if the number of students in course j is greater than or equal to the given minimum number s
    z = {}
    for j in range(len(courses)):
        z[j] = m.add_var(var_type=CONTINUOUS, ub=1, name="z_{}_{}".format(i, j))

    # set objective function:
    m.setObjective((xsum(xsum(10000 * c[i][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))) +
                    1000 * xsum(z[j] for j in range(len(courses))) +
                    1 * (xsum(xsum(d[i][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses)))) +
                    0.001 * (xsum(xsum(e[i][j] * x[(i, j)] for i in range(len(students))) for j in range(len(courses))))),
                   GRB.MAXIMIZE)

    # add constraints
    m.addConstrs((xsum(x[i, j] for j in range(len(courses))) <= 1 for i in range(len(students))), name="at_most_one_student")
    # ensures that student i is only asigned to one course j
    m.addConstrs((xsum(q[i][j] * x[(i, j)] for j in range(len(courses))) == 0 for i in range(len(students))),
                 name="one_course_per_student")
    # ensures that student i is only assigned to a chosen course j
    m.addConstrs((xsum(x[(i, j)] for i in range(len(students))) <= sub_max[j] * (1 - z[j]) for j in range(len(courses))), name="course_maximum")
    # ensures that the number of students in one course is less than or equal to the maximum number of participants
    m.addConstrs((sub_min[j] * (1 - z[j]) <= xsum(x[(i, j)] for i in range(len(students))) for j in range(len(courses))), name="course_minimum")
    # ensures that the number of students in one course is more than or equal to the minimum number of participants
    # if z_j is 1, the course j is cancelled
    return m, x, z