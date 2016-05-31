"""
Read a melodomatic script file and generate HTML documentation from its comments and code.
"""
import sys, os, argparse, re, cgi
import markdown

RE_LEADING_COMMENT = re.compile('^#\s*')
RE_TRAILING_COMMENT = re.compile('#*\s*$')
RE_HEADER = re.compile(r'^#{2,}\s*([^#]+)\s*#*\s*$')

# Split the script into a series of side-by-side comment and code chunks.
def collate(lines):
    rv = []
    collate.title = ''
    collate.cur = { 'comment':'', 'code':'' }
    def close_block():
        if collate.cur['comment'] or collate.cur['code']:
            rv.append(collate.cur)
        collate.cur = { 'comment':'', 'code':'' }
    for linei,line in enumerate(lines):
        line = line.rstrip()
        if len(line) == 0:
            collate.cur['code'] = ' '
            close_block()
        elif line[0] == '#':
            if not collate.title:
                collate.title = RE_HEADER.sub('\\1', line)
            line = RE_LEADING_COMMENT.sub('', line)
            line = RE_TRAILING_COMMENT.sub('', line)
            collate.cur['comment'] +=  line.strip() + '\n'
        else:
            collate.cur['code'] = line
            close_block()
    close_block()
    return rv,collate.title

def format(template, fn, title, blocks):
    # extract the sub-template for blocks from the template body.
    lines = template.split('\n')
    bstart = bend = -1
    for linei,line in enumerate(lines):
        if line.find('$BLOCKSTART') != -1:
            bstart = linei
        if line.find('$BLOCKEND') != -1:
            bend = linei
    btemplate = '\n'.join(lines[bstart:bend+1]) + '\n'
    # Replace the sub-template with a placeholder for the total results.
    del lines[bstart:bend+1]
    lines.insert(bstart, '$BLOCKS')
    template = '\n'.join(lines)

    btext = ''
    for block in blocks:
        comment = block['comment'].decode('utf-8')
        comment = markdown.markdown(comment)
        code = block['code'].decode('utf-8')
        code = cgi.escape(code)
        s = btemplate.replace('$COMMENT', comment.encode('ascii', 'xmlcharrefreplace'))
        s = s.replace('$CODE', code.encode('ascii', 'xmlcharrefreplace'))
        btext += s

    rv = template.replace('$FILENAME', fn)
    rv = rv.replace('$TITLE', title)
    rv = rv.replace('$BLOCKS', btext)
    return rv

def document(templatefn, inputfn):
    tfp = open(templatefn)
    template = tfp.read()
    tfp.close()

    fp = open(inputfn)
    lines = fp.readlines()
    fp.close()
    blocks,title = collate(lines)

    fnTrim = os.path.basename(inputfn)
    return format(template, fnTrim, title, blocks).encode('utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+', help='Melodomatic scripts to be docified')
    parser.add_argument('--template','-t', dest='template', action='store', help='Template file')
    args = parser.parse_args()

    tfn = os.path.join(os.path.dirname(__file__), 'meloDOCmatic_template.html')
    if args.template:
        tfn = args.template
    for ifn in args.file:
        print document(tfn, ifn)

