from cgi import test
import os
import argparse


def generate_new_file(test_dir, output_dir):
    
    os.makedirs(output_dir, exist_ok=True)
    
    # copy all of the things in models to one place
    models_dict = {}
    with open(os.path.join(output_dir, 'utils.py'), 'w') as fp:
        fp.write('import pytest\n\n\n')
        for dirpath, _, filenames in os.walk(test_dir):
            path = dirpath.split('/')
            if 'models' in path:
                # make sure the path exists in 
                model_dict_path = path[path.index('models') + 1:]
                write_place = models_dict
                for dir in model_dict_path:
                    if '"' + dir + '"' not in write_place:
                        write_place['"' + dir + '"'] = {}
                    write_place = write_place['"' + dir + '"']
                # convert all the files to string
                # add it to models dict
                for filename in filenames:
                    string_name = filename.replace('.', '_')
                    fp.write(string_name + ' = """\n')
                    with open(os.path.join(dirpath, filename)) as f:
                        for line in f.readlines():
                            fp.write(line)
                    fp.write('"""\n\n')
                    write_place['"' + filename + '"'] = string_name
        fp.write('@pytest.fixture\ndef models():\n    return ')
        fp.write(str(models_dict).replace('\'', ''))
    os.system("black %s" % os.path.join(output_dir, 'models.py'))

    # create new python files
    python_files = []
    for _, _, filenames in os.walk(test_dir):
        for filename in filenames:
            if filename.startswith('test') and filename.endswith('.py'):
                python_files.append(filename)
                with open(os.path.join(output_dir,filename), 'w') as fp:
                    fp.write("""
import pytest

from dbt.tests.util import run_dbt
from tests.%s.utils import models
                    """ % '.'.join(output_dir.split('/')[-2:]))

                
                
                

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='helper for converting original tests to pytest')
    parser.add_argument('--test_dir', type=str,
                        help='directory of the test to covert')
    parser.add_argument('--output_dir', type=str,
                        help='directory to write the converted test to')

    args = parser.parse_args()

    generate_new_file(args.test_dir, args.output_dir)
