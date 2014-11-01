# Topydo - A todo.txt client written in Python.
# Copyright (C) 2014 Bram Schoenmakers <me@bramschoenmakers.nl>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

from Command import *
from PrettyPrinter import *
from Recurrence import advance_recurring_todo
from TodoList import InvalidTodoException
from Utils import convert_todo_number, InvalidTodoNumberException

class DoCommand(Command):
    def __init__(self, p_args, p_todolist,
                 p_out=lambda a: None,
                 p_err=lambda a: None,
                 p_prompt=lambda a: None):
        super(DoCommand, self).__init__(p_args, p_todolist, p_out, p_err, p_prompt)

        self.number = None
        self.force = self.argument_shift("--force") or self.argument_shift("-f")

        try:
            self.number = convert_todo_number(self.argument(0))
            self.todo = self.todolist.todo(self.number)
        except (InvalidCommandArgument, InvalidTodoNumberException, InvalidTodoException):
            self.todo = None

    def _uncompleted_children(self, p_todo):
        return sorted([t for t in self.todolist.children(p_todo) if not t.is_completed()])

    def _print_list(self, p_todos, p_print_numbers=True):
        filters = []

        if p_print_numbers:
            filters = [self.todolist.pp_number()]

        self.out("\n".join(pretty_print_list(p_todos, filters)))

    def _complete_children(self):
            children = self._uncompleted_children(self.todo)
            if children:
                self._print_list(children)

                if not self.force:
                    confirmation = self.prompt("Also mark subtasks as done? [n] ")

                if not self.force and re.match('^y(es)?$', confirmation, re.I):
                    for child in children:
                        self.todolist.set_todo_completed(child)
                        self.out(pretty_print(child))

    def _handle_recurrence(self):
        if self.todo.has_tag('rec'):
            new_todo = advance_recurring_todo(self.todo)
            self.todolist.add_todo(new_todo)
            self.out(pretty_print(new_todo, [self.todolist.pp_number()]))

    def _print_unlocked_todos(self):
        """
        Print the items that became unlocked by marking this subitem
        (self.todo) as complete.
        """
        parents = [parent for parent in self.todolist.parents(self.todo) if not self._uncompleted_children(parent) and parent.is_active()]

        if parents:
            self.out("The following todo item(s) became active:")
            self._print_list(parents, False)

    def execute(self):
        if not super(DoCommand, self).execute():
            return False

        if not self.number:
            self.error(self.usage())
        elif self.todo and not self.todo.is_completed():
            self._complete_children()
            self._handle_recurrence()
            self.todolist.set_todo_completed(self.todo)
            self.out(pretty_print(self.todo))
            self._print_unlocked_todos()
        elif not self.todo:
            self.error("Invalid todo number given.")
        else:
            self.error("Todo has already been completed.")

    def usage(self):
        return """Synopsis: do [--force] <NUMBER>"""

    def help(self):
        return """Marks the todo with given number as complete.

In case the todo has subitems, a question is asked whether the subitems should
be marked as completed as well. When --force is given, no interaction is
required and the subitems are not marked completed.

In case the completed todo is recurring, a new todo will be added to the list,
while the given todo item is marked as complete."""