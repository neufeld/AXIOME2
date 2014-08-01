from os import getcwd
from os.path import dirname, abspath

def copySampleAxFile():
    '''Copies the sample Ax, updating the filepaths in the process'''
    #Finds the install directory, from which the res folder can be found
    source_dir = dirname(abspath(__file__))
    sample_file = source_dir + "/res/sample/sample.ax"
    cwd = getcwd()
    with open(sample_file, "r") as sample_in:
        with open("sample.ax", "w") as sample_out:
            for line in sample_in:
                sample_out.write(line.replace("@SOURCE_DIR@",source_dir))
