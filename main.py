import click
from data_reader import read_data
from create_model import create_model
from print_solution import print_and_write_solution
import time
from mip import *

@click.command()
@click.argument('instancename')
@click.option('-c', '--hard-constraint', type=bool, default=True)

def main(instancename: str, hard_constraint: bool):
    start = time.time()

    items, choices, settings, conflicts, categories = read_data(instancename)
    m, x, z, q = create_model(items, choices, settings, conflicts, categories, hard_constraint)

    m.write(instancename+'/{}.lp'.format(instancename))

    m.optimize()
    print_and_write_solution(m, x, z, q, items, choices, instancename, settings)
    print('time', time.time() - start)


if __name__ == '__main__':
    main()

