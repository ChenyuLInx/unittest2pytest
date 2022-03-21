"""
fix_remove_class - lib2to3 fix for removing "class Testxxx(TestCase):"
headers and dedenting the contained code.
"""
#
# Copyright 2015-2019 by Hartmut Goebel <h.goebel@crazy-compilers.com>
#
# This file is part of unittest2pytest.
#
# unittest2pytest is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

__author__ = "Hartmut Goebel <h.goebel@crazy-compilers.com>"
__copyright__ = "Copyright 2015-2019 by Hartmut Goebel"
__licence__ = "GNU General Public License version 3 or later (GPLv3+)"


# from dbt.tests.fixtures.project import model_path
from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import token, find_indentation
from lib2to3.pytree import Leaf
from lib2to3.pytree import Node

"""
Node(classdef, 
     [Leaf(1, 'class'), 
      Leaf(1, 'TestAssertEqual'), 
      Leaf(7, '('), 
      Leaf(1, 'TestCase'), 
      Leaf(8, ')'), 
      Leaf(11, ':'), 
      Node(suite, [
          Leaf(4, '\n'), 
          Leaf(5, '    '), 
          Node(funcdef, [
              Leaf(1, 'def'), 
              Leaf(1, 'test_you'), ...
          ]), 
          Leaf(6, '')])])
"""


def delete_multiple_element(list_object, indices):
    indices = sorted(indices, reverse=True)
    for idx in indices:
        if idx < len(list_object):
            list_object.pop(idx)

def selector_update_func(node):
    node.children[4].children[2].children[0].children[1] = node.children[4].children[2].children[0].children[1].children[2].children[1]

class FixFunctions(BaseFix):

    PATTERN = """
      classdef< 'class' name=any '(' any ')' ':'
         suite=suite
      >
    """

    def dedent(self, suite):
        for kid in suite.leaves():

            if kid.value == 'def':
                kid.prefix = ''
            

    def transform(self, node, results):
        suite = results['suite']
        
        # todo: handle tabs
        self.dedent(suite)

        # remove the first newline behind the classdef header
        # first = suite.children[0]
        # if first.type == token.NEWLINE:
        #     if len(first.value) == 1:
        #         del suite.children[0]
        #     else:
        #         first.value == first.value[1:]

        # # remove tab, issue with this is that it only removes the first one
        # suite.children = [c for c in suite.children if c.type != 5]


        # remove integration Test inheretance
        # deal with single and multiple inherent
        if node.children[3].type != 260:
            parent_classes = [node.children[3]]
        else:
            parent_classes = node.children[3].children

        parent_classes_to_remove = ['DBTIntegrationTest']
        for idx, parent_class in enumerate(parent_classes):
            if parent_class.value in parent_classes_to_remove:
                parent_class.value = ''
                # remove , before and after the removed class
                if idx < len(node.children[3].children) - 1 :
                    node.children[3].children[idx + 1].value = ''
                if idx > 0:
                    node.children[3].children[idx - 1].value = ''


        # remove all decorator
        for child in suite.children:
            child.children = [c for c in child.children if c.type != 278]
        

        functions_to_remove = ['schema']
        function_name_map = {
            'project_config': 'project_config_update',
            'selectors_config': 'selectors',
            'profile_config': 'profiles_config_update',
            'models': 'model_path',
            'packages_config': 'packages',
            'setUp': 'setup'
        }
        auto_use_fixture = ['setup']
        function_process_map = {
            'selectors': selector_update_func
        }
        remove_idxes = []

        for i, child in enumerate(suite.children):
            # if it is a decorator, go down a level
            if child.type == 277:
                child = child.children[0]

            # if it is a function definition, start doing something
            if child.type == 295:
                function_def = child
                parameters = function_def.children[2]
                function_name = function_def.children[1]
                # print('=====%s====='%function_name)

                if function_name.value in functions_to_remove:
                    remove_idxes.append(i)
                
                # replace functions
                if function_name.value in function_name_map:
                    function_name.value = function_name_map[function_name.value]
                    
                    func_node = child.clone()
                    func_node.parent = None
                    if function_name.value in function_process_map:
                        function_process_map[function_name.value](func_node)
                    # add a decorater in front by modify the def string
                    dec = '@pytest.fixture(scope="class")\n    '
                    if function_name.value in auto_use_fixture:
                        dec = '@pytest.fixture(scope="class", autouse=True)\n    '
                    func_node.children[0].value = dec + func_node.children[0].value

                    suite.children[i] = func_node
                    continue

                # this will add project fixture to test, sometime the function will be passed twice so we skip the second time
                if function_name.value.startswith('test') and parameters.children[2].value != ' project, ':
                    project_arg = parameters.children[1].clone()
                    project_arg.value = ' project, '
                    parameters.children[1].value += ','
                    parameters.children.insert(2, project_arg)
                    # project_arg = parameters.children[1].clone()
                    # project_arg.value = ' project_files'
                    # parameters.children.insert(3, project_arg)

                # all things defined in a function
                function_content = function_def.children[4]
                
                if 'postgres' in function_name.value:
                    function_name.value = function_name.value.replace('__postgres__', '_')
                    function_name.value = function_name.value.replace('_postgres_', '_')
                
                # Update the functions that get changed between previous tests and current test
                prev_is_self = False
                for leaf in function_content.leaves():
                    # remove . after self
                    # if prev_is_self and leaf.type == 23:
                    #     leaf.value = ''
                    # if leaf.value == 'self':
                    #     leaf.value = ''
                    #     prev_is_self = True
                    # else:
                    #     prev_is_self = False 
                    
                    # remove self. in front of run_dbt
                    if leaf.value == 'run_dbt':
                        leaf.prev_sibling.value = ''
                        leaf.parent.parent.children[0].value = ''
                    # this would add project. in the beginning of run_sql_file
                    if leaf.value == 'run_sql_file':
                        leaf.parent.parent.children[0].value = 'project'
                    
                    # this would add table_comp. in the beginning of assertTablesEqual
                    if leaf.value == 'assertTablesEqual':
                        # leaf.prev_sibling.value = '.'
                        leaf.parent.parent.children[0].value = 'table_comp'
                    
                    # if you want to replace a function(used inside function), can do it by
                    # if leaf.value == 'original name':
                    #     leaf.value == 'replaced name'

        delete_multiple_element(suite.children, remove_idxes)
         

        # return suite