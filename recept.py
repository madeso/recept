#!/usr/bin/env python3

import argparse
import typing
import os
import shutil
import time

import pystache
import markdown
import yaml

from stringlistcombiner import StringListCombiner

FRONTMATTER_SEPERATOR_CHAR = '+'
FRONTMATTER_SEPERATOR_MIN_LENGTH = 3

class Args:
    def __init__(self, is_debug: bool):
        self.is_debug = is_debug

    def debug_print(self, text: str):
        if self.is_debug:
            print(text)


def file_exist(file: str) -> bool:
    return os.path.isfile(file)


def read_frontmatter_file(path: str, missing_is_error: bool = True) -> typing.Tuple[str, str]:
    has_frontmatter = False
    first = []
    second = []
    if not missing_is_error and not file_exist(path):
        return (None, '')
    with open(path, 'r', encoding='utf-8') as inputfile:
        for line in inputfile:
            if not has_frontmatter:
                s = line.strip()
                if len(s) >= FRONTMATTER_SEPERATOR_MIN_LENGTH and len(s) * FRONTMATTER_SEPERATOR_CHAR == s:
                    has_frontmatter = True
                else:
                    first.append(line)
            else:
                second.append(line)
        if has_frontmatter:
            return (''.join(first), ''.join(second))
        else:
            return ('', ''.join(first))



def add_file_arguments(parser):
    parser.add_argument('--output', help='the folder where to write to', default=os.path.join(os.getcwd(), 'public'))


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
    for (dirpath, _, filenames) in os.walk(mypath):
        for filename in filenames:
            if os.path.splitext(filename)[1] in ext:
                yield os.path.join(dirpath, filename)


def run_markdown(contents: str):
    # replace 1/2 with ½
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


def handle_watch(_):
    while True:
        # book = get_book(args.folder)
        # stat = Stat()
        # format_files(None, True, book, extension, stat)
        # check_sass(book)
        time.sleep(0.3)


class Cat:
    def __init__(self, name: str):
        self.recept = []
        self.name = name


class Categories:
    def __init__(self):
        self.common = {}
        self.extra = {}

    def add_commons(self, names: typing.List[str]):
        for name in names:
            if name not in self.common:
                self.common[name] = Cat(name)

    def add(self, names: typing.List[str], r: 'Recept'):
        for name in names:
            if name in self.common:
                self.common[name].recept.append(r)
            elif name in self.extra:
                self.extra[name].recept.append(r)
            else:
                c = Cat(name)
                c.recept.append(r)
                self.extra[name] = c


    def iterate_names(self):
        for name in self.common:
            yield name

        for name in self.extra:
            yield name

    def iterate_cats(self):
        for _, c in self.common.items():
            yield c

        for _, c in self.extra.items():
            yield c



def create_categories() -> Categories:
    cat = Categories()
    cat.add_commons(['Mat', 'Soppa', 'Dricka', 'Picnic', 'Efterrätt'])
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
        # print('Changing link', l, newl)
        return newl
    else:
        return l


def cat_link(c: Cat) -> str:
    return 'cats/' + c.name + '.html'


class Template:
    def __init__(self, path: str):
        self.path = path
        with open(path) as f:
            self.content = f.read()

    def base_data(self, recept_categories: typing.List[str], cat: Categories):
        data = {}
        categories = lambda names: [{'name': name, 'selected': name in recept_categories, 'link': cat_link(c)} for name, c in names.items()]
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
        data['recept'] = [{'title': r.title, 'link': urllink(r), 'category': slc(r.categories)} for r in recept]

        output = pystache_render(self.path, self.content, data)
        return output

    def render_cat(self, cat: Cat, cats: Categories):
        data = self.base_data([cat.name], cats)
        data['recept'] = [{'title': r.title, 'category': slc(r.categories), 'link': urllink(r)} for r in cat.recept]
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
            line = self.read()
            if line == '|':
                return r
            r.append(line)

        return r


def file_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]



def load_front_matter(lines: str, path: str) -> typing.Dict[str, str]:
    def on_key(r: typing.Dict[str, str], key: str, value: str):
        if key in r:
            r[key] = r[key] + '\n' + value
        else:
            r[key] = value
    r = {}
    key = None
    line_number = 0

    for sline in lines.splitlines() if lines is not None else []:
        line_number = line_number + 1
        line = sline.lstrip()
        if len(sline) != len(line) and key is not None:
            on_key(r, key, line)
        else:
            if len(line) == 0:
                if key is not None:
                    on_key(r, key, '')
                continue
            if key is not None:
                on_key(r, key, '')
                key = None
            spl = line.split(':', maxsplit=1)
            if len(spl) == 2:
                k = spl[0].strip()
                v = spl[1].strip()
                if len(v) == 0:
                    key = k
                else:
                    on_key(r, k, spl[1])
            else:
                print('{}({}): Syntax error, missing colon in line: {}'.format(path, line_number, line))
    if key is not None:
        on_key(r, key, '')

    return r


def is_true(file: str, val_case: str) -> bool:
    val = val_case.lower()
    if val in ['true', 'yes', '1']:
        return True
    elif val in ['false', 'no', '0']:
        return False
    else:
        print('{}: "{}" is not a known boolean'.format(file, val_case))
        return False



def parse_recept_file(args: Args, path: str) -> Recept:
    args.debug_print('Parsing file {}'.format(path))

    fm, content = read_frontmatter_file(path)
    data = load_front_matter(fm, path)

    title = get_frontmatter(data, 'title')

    categories = [c.strip() for c in (get_frontmatter(data, 'categories') or '').split(',')]
    image = (get_frontmatter(data, 'image') or '').strip()
    description = run_markdown(get_frontmatter(data, 'description') or '').strip()
    favorite = is_true(path, (get_frontmatter(data, 'favorite') or 'false').strip())
    tagdata = (get_frontmatter(data, 'tags') or '').strip().split('#')
    tags = [l.strip() for l in tagdata if len(l.strip()) > 0]

    sections = []

    lines = Reader([l.strip() for l in content.splitlines()])
    while lines.has_more():
        lines.skip_empty()
        ingredients = lines.read_section()
        lines.skip_empty()
        steps = lines.read_section()
        sections.append(Section(ingredients, steps))

    recept = Recept(file_name(path), title, categories, image, description, sections, favorite, tags)

    return recept


def get_frontmatter(frontmatter, name: str):
    if frontmatter is None:
        return None
    return frontmatter[name] if name in frontmatter else None


def parse_md_file(path) -> Recept:
    print('Parsing', path)
    with open(path) as f:
        lines = Reader([l for l in f][1:])

        frontmatter_source = []
        while lines.has_more() and lines.peek().strip() != '---':
            frontmatter_source.append(lines.read())
        lines.read()

        frontmatter = yaml.load(''.join(frontmatter_source), Loader=yaml.Loader)
        content = ''.join(lines.lines)

        frontmatter_tags = get_frontmatter(frontmatter, 'tags') or []

        favorite = 'Favorit' in frontmatter_tags

        return Recept(file_name(path), get_frontmatter(frontmatter, 'title') or '', get_frontmatter(frontmatter, 'category') or [], '', run_markdown(content), [], favorite, frontmatter_tags)



def parse_file(args: Args, path: str) -> Recept:
    ext = os.path.splitext(path)[1]
    if ext == '.recept':
        return parse_recept_file(args, path)
    elif ext == '.md':
        return parse_md_file(path)
    else:
        print('Unknown extension', ext)
        return None


def handle_test(args):
    recept = parse_file(Args(args.debug), args.file)
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
    recept = parse_file(Args(args.debug), input_file(args.file))
    template = Template(input_file('recept.html'))
    with open(output_file(args, 'index.html'), 'w') as f:
        output = template.render(recept, create_categories())
        print(output, file=f)


def handle_paths(args):
    print(input_file('input.txt'))
    print(output_file(args, 'output.txt'))


def generate_project(aargs: Args, args, input_folder: str, index_template: Template, output_template: Template, cat_template: Template, markdown: bool):
    patterns = ['.recept']
    if markdown:
        patterns.append('.md')
    recept = [parse_file(aargs, file) for file in list_files(input_folder, patterns)]

    cat = create_categories()

    for r in recept:
        cat.add(r.categories, r)

    aargs.debug_print('writing index')
    with open(output_file(args, 'index.html'), 'w') as f:
        output = index_template.render_index(recept, cat)
        print(output, file=f)

    aargs.debug_print('writing cats')
    for c in cat.iterate_cats():
        with open(output_file(args, cat_link(c)), 'w') as f:
            output = cat_template.render_cat(c, cat)
            print(output, file=f)

    for r in recept:
        file_name = link(r)
        aargs.debug_print('writing {}'.format(file_name))
        with open(output_file(args, file_name), 'w') as f:
            output = output_template.render(r, cat)
            print(output, file=f)
        if r.image != '':
            image_relative = output_file(args, os.path.join(urllink(r), r.image))
            image_source = input_file(os.path.join('static', 'recept', r.image))
            aargs.debug_print('copying image {} {}'.format(image_source, image_relative))
            shutil.copy(image_source, image_relative)


def handle_generate(args):
    index_template = Template(input_file('index.html'))
    output_template = Template(input_file('recept.html'))
    cat_template = Template(input_file('cat.html'))

    generate_project(Args(args.debug), args, args.input, index_template, output_template, cat_template, args.markdown)


def safe_file_name(title: str) -> str:
    r = title
    r = r.lower()
    r = r.strip()
    r = r.replace(' ', '-')
    r = r.replace('å', 'a')
    r = r.replace('ä', 'a')
    r = r.replace('ö', 'o')
    r = r.replace('é', 'e')
    r = r.replace('è', 'e')
    r = r.replace('?', '')
    r = r.replace(',', '')
    r = r.replace('.', '')
    r = r.replace('!', '')
    return r


def handle_new(args):
    title = args.title
    name = safe_file_name(title)
    path = os.path.join(os.getcwd(), 'content', 'recept', name + '.recept')
    # print(title)
    # print(name)
    # print(path)
    content = []
    content.append('title: ' + title)
    content.append('category: Mat')
    content.append('tags: #hej')
    content.append('description: text')
    content.append('+++')
    content.append('')
    content.append('Ingrediens')
    content.append('|')
    content.append('Steg')

    with open(path, 'w') as f:
        print('\n'.join(content), file=f)
    print(path)


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
    sub.add_argument('--no-markdown', dest='markdown', action='store_false')
    sub.add_argument('--input', help='the input folder', default=os.getcwd())
    sub.add_argument('--debug', action='store_true')
    sub.set_defaults(func=handle_generate)

    sub = sub_parsers.add_parser('test', help='Parse a recept file')
    add_file_arguments(sub)
    sub.add_argument('file', help='the file to test')
    sub.add_argument('--debug', action='store_true')
    sub.set_defaults(func=handle_test)

    sub = sub_parsers.add_parser('new', help='Create a new recept file')
    sub.add_argument('title', help='the title of the recept')
    sub.set_defaults(func=handle_new)

    sub = sub_parsers.add_parser('render', help='Parse and render a recept file')
    add_file_arguments(sub)
    sub.add_argument('file', help='the file to test')
    sub.add_argument('--debug', action='store_true')
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
