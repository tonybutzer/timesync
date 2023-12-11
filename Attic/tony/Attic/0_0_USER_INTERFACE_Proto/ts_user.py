import argparse

def _mkdir(directory):
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)

def get_parser():
    parser = argparse.ArgumentParser(description='Run the eto code')
    parser.add_argument('project_id', metavar='project_id', type=str, 
            help='the project_id to process - example: 3132')
    parser.add_argument('-r', '--year', help='specify year or Annual or all example: -r 1999 ', default='1984', type=str)
    parser.add_argument('-x', '--x', help='x coordinate for timesync', type=int, required=True)
    parser.add_argument('-y', '--y', help='y coordinate for timesync', type=int, required=True)
    parser.add_argument('-p', '--plot_id', help='plot_id 1 .. 200 ' , default='1', type=str, required=True)
    parser.add_argument('-s', '--strata', help='strata - so far  not used  ' , default='41', type=str)
    return parser


def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())


    print(args)

    return True


if __name__ == '__main__':
    #_mkdir('log')
    #log = log_init('ET_MOSAIC', 'DEBUG')

    command_line_runner()
