#!/usr/bin/env python3

import argparse
import typing
import os

import pystache
import markdown


def run_markdown(contents: str):
    body = markdown.markdown(contents, extensions=['extra', 'def_list', 'codehilite'])
    body = body.replace('<aside markdown="1"', '<aside')
    return body


def check(from_path, to_path):
    sourcemod = os.path.getmtime(from_path)
    destmod = os.path.getmtime(to_path)
    if sourcemod < destmod:
        return False

    return True


def run_template():
    data = {}
    data['title'] = title_text
    data['section_header'] = section_header
    data['header'] = chapter.title
    data['body'] = body
    data['prev'] = prev_link
    data['next'] = next_link
    data['book_title'] = book.title
    data['copyright'] = book.copyright

    output = pystache_render(chapter.href, template, data)


def handle_watch(args):
    while True:
        # book = get_book(args.folder)
        # stat = Stat()
        # format_files(None, True, book, extension, stat)
        # check_sass(book)
        time.sleep(0.3)


class Section:
    def __init__(self, ingredients, steps):
        self.ingredients = ingredients
        self.steps = steps


class Recept:
    def __init__(self, title: str, image: str, description, sections):
        self.title = title
        self.image = image
        self.description = description
        self.sections = sections


class Reader:
    def __init__(self, lines):
        self.lines = lines

    def has_more(self) -> bool:
        return len(self.lines) > 0

    def peek(self) -> str:
        if self.has_more():
            return self.lines[0]
        else:
            return ''
    
    def peek_empty(self) -> bool:
        return self.peek().strip() == ''

    def read(self) -> str:
        if self.has_more():
            r = self.peek()
            self.lines = self.lines[1:]
            return r
        else:
            return ''
    
    def skip_empty(self):
        while self.has_more() and self.peek().strip() == '':
            self.read()

    def read_section(self):
        r = []

        while not self.peek_empty():
            r.append(self.read())
        
        return r



def parse_file(path) -> Recept:
    with open(path) as f:
        lines = Reader([l.strip() for l in f])
        
        title = lines.read()
        image = '' if lines.peek_empty() else lines.read()
        description = lines.read_section()
        
        sections = []
        while lines.has_more():
            lines.skip_empty()
            ingredients = lines.read_section()
            lines.skip_empty()
            steps = lines.read_section()
            sections.append(Section(ingredients, steps))

        recept = Recept(title, image, ''.join(description).strip(), sections)

        return recept


def handle_test(args):
    recept = parse_file(args.file)
    print('Title:', recept.title)
    print('Image:', recept.image)
    if recept.description != '':
        print('Descrption:', recept.description)
    print()
    for s in recept.sections:
        for i in s.ingredients:
            print('*', i)
        for i, s in enumerate(s.steps):
            print('{}.'.format(i+1), s)
        print()


def main():
    parser = argparse.ArgumentParser(description='Create or write a recept')
    sub_parsers = parser.add_subparsers(dest='command_name', title='Commands', help='', metavar='<command>')

    # sub = sub_parsers.add_parser('watch', help='Watch file for changes')
    # sub.add_argument('--folder', help='the folder where to run from', default=os.getcwd())
    # sub.set_defaults(func=handle_watch)

    # sub = sub_parsers.add_parser('build', help='Build recept')
    # sub.add_argument('--folder', help='the folder where to run from', default=os.getcwd())
    # sub.add_argument('--filter', help='specify a file name filter to just regenerate a subset of the files')
    # sub.set_defaults(func=handle_build)

    sub = sub_parsers.add_parser('test', help='Parse a recept file')
    sub.add_argument('--folder', help='the folder where to run from', default=os.getcwd())
    sub.add_argument('file', help='the file to test', default=os.getcwd())
    sub.set_defaults(func=handle_test)

    args = parser.parse_args()
    if args.command_name is not None:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

