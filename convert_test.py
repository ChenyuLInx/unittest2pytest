from cgi import test
import os
import shutil
import argparse


def write_dir_fixture(fp, dir_name, dir_dic):
    fp.write('@pytest.fixture\ndef %s():\n    return ' % dir_name.replace('-', '_'))
    fp.write(str(dir_dic).replace('\'', ''))
    fp.write('\n\n')

def generate_new_file(test_dir, output_dir):
    
    os.makedirs(output_dir, exist_ok=True)
    
    # convert all the dir with files in it to pytest fixture

    # this is the place that stores the dir structure of test repo
    all_dir = {}
    with open(os.path.join(output_dir, 'fixtures.py'), 'w') as fp:
        test_dir_name = test_dir.split('/')[-1]
        
        # basic import at the top of the file
        fp.write('import pytest\n')
        fp.write('from dbt.tests.fixtures.project import write_project_files\n\n\n')

        for dirpath, _, filenames in os.walk(test_dir):
            curr_path = dirpath.split('/')

            # skip test root dir, cache dirs and empty dirs
            if curr_path[-1] != test_dir_name and not curr_path[-1].endswith('__') and filenames:

                # curr dir entry is the top level dir name in a test project for the current dirpath
                curr_dir_entry_name = curr_path[curr_path.index(test_dir_name) + 1]
                # add current dir entry name to all_dir if it is not there
                if curr_dir_entry_name not in all_dir:
                    all_dir[curr_dir_entry_name] = {}

                # traverse through all_dir to build dictionary path to current dir
                write_place = all_dir[curr_dir_entry_name]
                model_dict_path = curr_path[curr_path.index(test_dir_name) + 2:]
                for dir in model_dict_path:
                    if '"' + dir + '"' not in write_place:
                        write_place['"' + dir + '"'] = {}
                    write_place = write_place['"' + dir + '"']

                # convert all the files to string
                # and add the file in all_dir
                for filename in filenames:
                    if not filename.endswith('pyc'):
                        whole_file_path = os.path.join(*curr_path[curr_path.index(test_dir_name) + 1:], filename)
                        string_name = whole_file_path.replace('.', '_').replace('/', '__').replace('-', '_')
                        fp.write(string_name + ' = """\n')
                        with open(os.path.join(dirpath, filename)) as f:
                            for line in f.readlines():
                                fp.write(line)
                        fp.write('"""\n\n')
                        write_place['"' + filename + '"'] = string_name
        # write all of the fixture for dirs in a project
        for dir_name, dir_dict in all_dir.items():
            write_dir_fixture(fp, dir_name, dir_dict)
        
        # create the project_files fixture
        fp.write('@pytest.fixture\ndef project_files(project_root,')
        for dir_name in all_dir.keys():
            fp.write(' %s,' % dir_name.replace('-', '_'))
        fp.write('):\n')
        # write_project_files(project_root, "models", models)
        for dir_name in all_dir.keys():
            fp.write('    write_project_files(project_root, "%s", %s)\n' % (dir_name, dir_name.replace('-', '_')))
        fp.write('\n\n')
        



    # move seed.sql and create code to run it
    seed_copied = False
    for dirpath, _, filenames in os.walk(test_dir):
        for filename in filenames:
            if filename == 'seed.sql':
                os.makedirs(os.path.join(output_dir, 'data'), exist_ok=True)
                shutil.copyfile(os.path.join(dirpath,'seed.sql'), os.path.join(output_dir, 'data', 'seed.sql'))
                seed_copied = True
                break

    os.system("black %s" % os.path.join(output_dir, 'fixtures.py'))

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
from tests.%s.fixtures import project_files


                    """ % '.'.join(output_dir.split('/')[-2:]))
                    if seed_copied:
                        fp.write("""
# seed.sql copied, you can run it by
# project.run_sql_file(os.path.join(project.test_data_dir, "seed.sql"))

# if things in seed.sql is not very complex, you can also convert it to run
# using the standard seed fixture. example at
# https://github.com/dbt-labs/dbt-core/blob/main/tests/functional/graph_selection/fixtures.py#L173
                        """
                        )

                
                
                

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='helper for converting original tests to pytest')
    parser.add_argument('--test_dir', type=str,
                        help='directory of the test to covert')
    parser.add_argument('--output_dir', type=str,
                        help='directory to write the converted test to')

    args = parser.parse_args()

    generate_new_file(args.test_dir, args.output_dir)
