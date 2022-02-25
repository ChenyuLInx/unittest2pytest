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


from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import token, find_indentation

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

class FixRemoveClass(BaseFix):

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
        suite = results['suite'].clone()
        
        # todo: handle tabs
        self.dedent(suite)

        # remove the first newline behind the classdef header
        first = suite.children[0]
        if first.type == token.NEWLINE:
            if len(first.value) == 1:
                del suite.children[0]
            else:
                first.value == first.value[1:]

        # # remove tab, issue with this is that it only removes the first one
        # suite.children = [c for c in suite.children if c.type != 5]


        # remove all decorator
        for child in suite.children:
            child.children = [c for c in child.children if c.type != 278]
        
        for child in suite.children:
            # if it is a decorator, go down a level
            if child.type == 277:
                child = child.children[0]
            # if it is a function definition, start doing something
            if child.type == 295:
                function_def = child
                parameters = function_def.children[2]
                function_name = function_def.children[1]

                # this will replace self argument in test function definition to project
                if function_name.value.startswith('test'):
                    parameters.children[1].value = 'project'

                # all things defined in a function
                function_content = function_def.children[4]
                
                # this part removes self. in the code
                prev_is_self = False
                for leaf in function_content.leaves():
                    # remove . after self
                    if prev_is_self and leaf.type == 23:
                        leaf.value = ''
                    if leaf.value == 'self':
                        leaf.value = ''
                        prev_is_self = True
                    else:
                        prev_is_self = False 
                    
                    # this would add project. in the beginning of run_sql_file
                    if leaf.value == 'run_sql_file':
                        leaf.prev_sibling.value = '.'
                        leaf.parent.parent.children[0].value = 'project'
                    
                    # this would add table_comp. in the beginning of assertTablesEqual
                    if leaf.value == 'assertTablesEqual':
                        leaf.prev_sibling.value = '.'
                        leaf.parent.parent.children[0].value = 'table_comp'

                    # if you want to replace a function, can do it by 
                    # if leaf.value == 'original name':
                    #     leaf.value == 'replaced name'
                    

                

        return suite
