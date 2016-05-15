# Dict'O'nator - A dictation plugin for gedit.
# Copyright (C) <2016>  <Abhinav Singh>
#
# This file is part of Dict'O'nator.
#
# Dict'O'nator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dict'O'nator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Dict'O'nator.  If not, see <http://www.gnu.org/licenses/>.

from enum import Enum
import re

from dictonator.setlog import logger
import dictonator.text2num as text2num


# defining valid states for dictonator
class DictonatorStates(Enum):
    started = 0
    preparing = 1
    prepared = 2
    stopping = 3
    stopped = 4
    recognising = 5
    error = 6

    recognised = 7
    fatal_error = 8


class DictonatorActions:
    """This class handles all actions and how to decide them."""

    # defining the actions, format is command_identifier: "magic words to call it"
    actions = dict(start_dictation={"start dictation", "start dictator", "start speaking"},
                   continue_dictation={},
                   stop_dictation={"stop dictation", "stop dictator", "stop dictation"},
                   hold_dictation={"hold dictation", "hold dictator", "wait dictation"},
                   scroll_to_cursor={"scroll to cursor"},
                   goto_line={"go to line", "goto line"},
                   undo={"undo", "do undo"},
                   redo={"redo", "do redo"},
                   cut_clipboard={"cut clipboard", "cut clip board", "cut selection", "cut to clipboard"},
                   copy_clipboard={"copy clipboard", "copy to clipboard", "copy selection", "copy clip board"},
                   paste_clipboard={"paste clipboard", "paste clipboard", "paste from clipboard"},
                   delete_selection={"delete selection", "delete selected text"},
                   select_all={"select all", "select all text"},
                   sentence_end={"sentence end", "close sentence", "end sentence", "full stop", "put period"},
                   line_end={"end line", "close line", "input enter", "put enter", "next line"},
                   delete_line={"delete line", "delete last line"},
                   delete_word={"delete word", "delete last word"},
                   delete_sentence={"delete sentence", "delete this sentence", "delete current sentence", },
                   clear_document={"clear document", "empty document", "clear file", "empty file"},
                   new_document={"new document", "new file"},
                   save_document={"save document", "save file"},
                   save_as_document={"save as document", "save document as", "save as file", "save file as"},
                   close_document={"close document", "close file"},
                   force_close_document={"force close document", "force close file"},
                   exit={"exit editor", "exit gedit", "editor exit", "gedit exit", "close editor", "close gedit",
                         "quit editor"},
                   put={"put", "insert", "type", "input"},
                   )
    # a dictionary to know which all commands are repeatable
    repeatable_actions = (
        "delete_sentence", "delete_line", "delete_word", "undo", "redo", "line_end", "sentence_end",)

    # format to define is special_indentifier: "special value", "magic words to put special"
    special_chars = dict(question_mark={"?", "question mark"}, exclamation_mark={"!", "exclamation mark"},
                         full_stop={".", "full_stop"}, comma={",", "comma"},
                         new_line={"\n", "new line", "enter"}, tab={"\t", "tab", "tab space"},
                         quote={'"', "quotes"}, apostrophe={"'", "apostrophe"},
                         forward_slash={"/", "slash", "forward slash"}, backward_slash={"\\", "forward slash"},
                         colon={":", "colon"}, semi_colon={";", "semi colon", "semicolon"},
                         ampersand={"&", "ampersand"}, at_rate={"@", "atrate", "at rate"}, hash={"#", "hash"},
                         dollar={"$", "dollar"}, per_cent={"%", "percentage", "per cent", "percent"},
                         star={"*", "star", "multiply"}, hyphen={"-", "minus", "hyphen", "subtract", "subtraction"},
                         under_score={"_", "underscore", "under score"}, equal={"=", "equals", "equal to"},
                         plus={"+", "plus", "add", "addition"},
                         left_bracket={"(", "left bracket", "open bracket"},
                         right_bracket={")", "right bracket", "close bracker"},
                         )
    # format to define is digit_indentifier: "digit_value digit", "magic words to put digit"
    digits = dict(zero={"0 digit", "zero digit"}, one={"1 digit", "one digit"},
                  two={"2 digit", "two digit"}, three={"3 digit", "three digit"},
                  four={"4 digit", "four digit"}, five={"5 digit", "five digit"},
                  six={"6 digit", "six digit"}, seven={"7 digit", "seven digit"},
                  eight={"8 digit", "eight digit"}, nine={"9 digit", "nine digit"}
                  )

    @staticmethod
    def _clean_text(txt: str):
        # clean the text of any symbols, make it lowercase
        txt = txt.lower()
        clean_string = re.sub('\W+', ' ', txt)
        return clean_string

    @staticmethod
    def decide_action(txt: str):
        """
        Deciding actions, look for commands, and convert specials
        :param txt:
        :return: tuple: chooseact, num ,special
        chooseact is the choosen action, num is how many times to repeat it, special is the character to put
        """
        choosenact = "continue_dictation"
        special = ""
        num = 1
        clean_txt = DictonatorActions._clean_text(txt)
        # logger.debug(clean_txt)
        for act in DictonatorActions.actions:
            for string in DictonatorActions.actions[act]:
                if string in clean_txt:
                    # string is a substring of clean_txt because clean_txt will have numbers/times to repeat
                    choosenact = act
                    if choosenact in DictonatorActions.repeatable_actions:
                        # asserted that the action is a command, find number of times to do it.
                        if "times" not in txt and "time" not in txt and "repeat" not in txt:
                            # means that the user did not not want to repeat
                            num = 1
                        else:
                            num = DictonatorActions.get_number(clean_txt)
                        return choosenact, num, special
                    elif choosenact == "goto_line":
                        # might go to first line if invalid input
                        num = DictonatorActions.get_number(clean_txt)
                        return choosenact, num, special
                    elif choosenact == "put":
                        num, special = DictonatorActions._handle_put(txt)
        # the action is continue dictation, now we will look for put specials in it, send unclean txt
        if special == "" and choosenact == "put":
            # put command was not needed, put was in the sentence
            choosenact = 'continue_dictation'
        return choosenact, num, special

    @staticmethod
    def get_number(txt: str):
        """call this function for both knowing times for commands and for knowing times to put"""

        # list of numbers found, empty if none
        num_list = [int(s) for s in txt.split() if s.isdigit()]
        txt = DictonatorActions._clean_numbered_text(txt)
        try:
            num = text2num.conv_text2num(txt)
            num_list.append(num)
        except text2num.NumberException:
            logger.debug("NumberException")
            pass
        # return only the first number
        if len(num_list) > 0:
            return num_list[0]
        else:
            return 1

    @staticmethod
    def _clean_numbered_text(txt: str):
        # remove non number string from the text
        lis = txt.split(" ")
        for s in lis[:]:
            if s not in text2num.Small and s not in text2num.Magnitude:
                lis.remove(s)
                print(s)
        return " ".join(lis)

    @staticmethod
    def _handle_put(txt: str):
        if "digit" in txt:
            # digit input
            return DictonatorActions._find_digit(txt)
        return DictonatorActions._find_special(txt)

    @staticmethod
    def _find_digit(txt_with_digit: str):
        lis = txt_with_digit.split('digit')
        digit = DictonatorActions.get_number(lis[0])
        if "times" not in lis[1] and "time" not in lis[1]:
            # means that the user did not not want to repeat puts
            times = 1
        else:
            times = DictonatorActions.get_number(lis[1])
        return times, digit

    @staticmethod
    def _find_special(txt_with_special: str):
        special = ""
        if "times" not in txt_with_special and "time" not in txt_with_special:
            # user did not not want to repeat puts
            times = 1
        else:
            times = DictonatorActions.get_number(txt_with_special)
        # looking for specials
        for char in DictonatorActions.special_chars:
            for string in DictonatorActions.special_chars[char]:
                if string in txt_with_special:
                    special = char
                    return times, special
        return times, special