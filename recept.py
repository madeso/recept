#!/usr/bin/env python3

import argparse
import typing
import os

import pystache
import markdown

from stringlistcombiner import StringListCombiner


def add_file_arguments(parser):
    parser.add_argument('--output', help='the folder where to write to', default=os.path.join(os.getcwd(), 'generated'))


def input_file(path):
    return os.path.abspath(path)


def output_file(args, path):
    if os.path.isabs(path):
        return path
    output = os.path.abspath(args.output)
    result = os.path.join(output, path)
    folder = os.path.dirname(result)
    os.makedirs(folder, exist_ok=True)
    return result


def list_files(mypath: str, ext):
    """yield all paths in mypath that matches the ext extension"""
    for (dirpath, dirnames, filenames) in os.walk(mypath):
        for filename in filenames:
            if os.path.splitext(filename)[1] in ext:
                yield os.path.join(dirpath, filename)


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



def pystache_render(filename, template, data):
    renderer = pystache.renderer.Renderer(missing_tags='strict')
    try:
        return renderer.render(template, data)
    except pystache.context.KeyNotFoundError as e:
        print(filename, e)
        return ''


def handle_watch(args):
    while True:
        # book = get_book(args.folder)
        # stat = Stat()
        # format_files(None, True, book, extension, stat)
        # check_sass(book)
        time.sleep(0.3)


class Categories:
    def __init__(self):
        self.common = []
        self.extra = []
    
    def add_commons(self, names: typing.List[str]):
        for name in names:
            if name not in self.common:
                self.common.append(name)
    
    def add_extra(self, name: str):
        if name not in self.extra:
            self.extra.append(name)

    def add(self, names: typing.List[str]):
        for name in names:
            if name in self.common:
                pass
            else:
                self.add_extra(name)

    
    def iterate_names(self):
        for name in self.common:
            yield name
        
        for name in self.extra:
            yield name



def create_categories() -> Categories:
    cat = Categories()
    cat.add_commons(['Mat', 'Soppa', 'Dricka', 'Picnic', 'Efterrätt'])
    cat.add_extra('Burgare')
    cat.add_extra('Tacos')
    cat.add_extra('Mat')
    return cat


class Section:
    def __init__(self, ingredients, steps):
        self.ingredients = ingredients
        self.steps = steps


class Recept:
    def __init__(self, name: str, title: str, categories: str, image: str, description: str, sections, favorite, tags):
        self.name = name
        self.title = title
        self.categories = categories
        self.image = image
        self.description = description
        self.sections = sections
        self.favorite = favorite
        self.tags = tags


def slc(names: typing.List[str]) -> str:
    s = StringListCombiner(', ', ' och ', 'Ingen kategori')
    return s.combine(names)


def link(r: Recept) -> str:
    return 'recept/{}/index.html'.format(r.name)


def urllink(r: Recept) -> str:
    l = link(r)
    index_html = '/index.html'
    if l.endswith(index_html):
        newl = l[:-len(index_html)] + '/'
        print('Changing link', l, newl)
        return newl
    else:
        return l



class Template:
    def __init__(self, path: str):
        self.path = path
        with open(path) as f:
            self.content = f.read()
    
    def base_data(self, recept_categories: typing.List[str], cat: Categories):
        data = {}
        categories = lambda names: [{'name': name, 'selected': name in recept_categories} for name in names]
        data['common_categories'] = categories(cat.common)
        data['extra_categories'] = categories(cat.extra)
        return data

    def render(self, recept: Recept, cat: Categories):
        data = self.base_data(recept.categories, cat)

        data['title'] = recept.title
        data['image'] = recept.image
        data['favorite'] = recept.favorite
        data['description'] = recept.description if recept.description != '' else None
        data['tags'] = [{'tag': tag} for tag in recept.tags]
        data['has_tags'] = len(recept.tags) > 0
        sections = []
        for s in recept.sections:
            d = {}
            d['steps'] = [{'step': st} for st in s.steps]
            d['ingredients'] = [{'ingredient': i} for i in s.ingredients]
            sections.append(d)
        data['sections'] = sections

        output = pystache_render(self.path, self.content, data)
        return output

    def render_index(self, recept: typing.Iterable[Recept], cat: Categories):
        data = self.base_data('', cat)
        data['recept'] = [{'title': r.title, 'link': urllink(r), 'category': slc(r.categories), 'link': urllink(r)} for r in recept]

        output = pystache_render(self.path, self.content, data)
        return output


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


def is_command(str, cmd):
    if len(str) == 0:
        return False
    return str[0:1] == cmd


def file_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def parse_recept_file(path) -> Recept:
    with open(path) as f:
        lines = Reader([l.strip() for l in f])
        
        title = lines.read()
        categories = [c.trim() for c in lines.read().split(',')]
        image = '' if lines.peek_empty() else lines.read()
        description = lines.read_section()
        favorite = False
        tags = []
        
        sections = []
        while lines.has_more():
            lines.skip_empty()
            l = lines.peek().strip()
            if l == '*':
                lines.read()
                favorite = True
            elif is_command(l, '#'):
                for t in (l.strip() for l in lines.read().strip().split('#') if len(l.strip()) > 0):
                    tags.append(t)
            else:
                ingredients = lines.read_section()
                lines.skip_empty()
                steps = lines.read_section()
                sections.append(Section(ingredients, steps))

        recept = Recept(file_name(path), title, categories, image, ''.join(description).strip(), sections, favorite, tags)

        return recept


def parse_md_file(path) -> Recept:
    import yaml
    with open(path) as f:
        lines = Reader([l for l in f][1:])

        frontmatter_source = []
        while lines.has_more() and lines.peek().strip() != '---':
            frontmatter_source.append(lines.read())
        lines.read()
        
        frontmatter = yaml.load(''.join(frontmatter_source), Loader=yaml.Loader)
        content = ''.join(lines.lines)

        frontmatter_tags = frontmatter['tags'] or []

        favorite = 'Favorit' in frontmatter_tags

        return Recept(file_name(path), frontmatter['title'], frontmatter['category'] or [], '', run_markdown(content), [], favorite, frontmatter_tags)
        


def parse_file(path) -> Recept:
    ext = os.path.splitext(path)[1]
    if ext == '.recept':
        return parse_recept_file(path)
    elif ext == '.md':
        return parse_md_file(path)
    else:
        print('Unknown extension', ext)
        return None


def handle_test(args):
    recept = parse_file(args.file)
    print('Title:', recept.title)
    print('Categories:', recept.categories)
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


def handle_render(args):
    recept = parse_file(input_file(args.file))
    template = Template(input_file('recept.html'))
    with open(output_file(args, 'index.html'), 'w') as f:
        output = template.render(recept, create_categories())
        print(output, file=f)


def handle_paths(args):
    print(input_file('input.txt'))
    print(output_file(args, 'output.txt'))


def generate_project(args, input_folder: str, index_template: Template, output_template: Template):
    recept = [parse_file(file) for file in list_files(input_folder, ['.md', '.recept'])]

    cat = create_categories()

    for r in recept:
        cat.add(r.categories)

    print('writing index')
    with open(output_file(args, 'index.html'), 'w') as f:
        output = index_template.render_index(recept, cat)
        print(output, file=f)
    
    for r in recept:
        file_name = link(r)
        print('writing {}'.format(file_name))
        with open(output_file(args, file_name), 'w') as f:
            output = output_template.render(r, cat)
            print(output, file=f)


def handle_generate(args):
    index_template = Template(input_file('index.html'))
    output_template = Template(input_file('recept.html'))
    
    generate_project(args, args.input, index_template, output_template)


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

    sub = sub_parsers.add_parser('generate', help='Parse all files and generate output')
    add_file_arguments(sub)
    sub.add_argument('--input', help='the input folder', default=os.getcwd())
    sub.set_defaults(func=handle_generate)

    sub = sub_parsers.add_parser('test', help='Parse a recept file')
    add_file_arguments(sub)
    sub.add_argument('file', help='the file to test')
    sub.set_defaults(func=handle_test)

    sub = sub_parsers.add_parser('render', help='Parse and render a recept file')
    add_file_arguments(sub)
    sub.add_argument('file', help='the file to test')
    sub.set_defaults(func=handle_render)

    sub = sub_parsers.add_parser('paths', help='debug write paths')
    add_file_arguments(sub)
    sub.set_defaults(func=handle_paths)

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

