"""Zotero meta-analysis toolkit

    Command-line tool to support meta-analysis using a library managed in
    Zotero.

    Copyright 2019-2021, Eric Thrift

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from dateutil.parser import parse as dateparse

import click
from pyzotero import zotero
import unicodecsv as csv

# def _strip_tag_prefix(tag):
#     new_tag = tag.strip('!@#$%^&*_')
#     if new_tag == '': # e.g., if the source tag is "!" or "**"
#         return tag
#     return new_tag

def _filter_tags(tags, prefixes):
    out = []
    for tag in tags:
        for prefix in prefixes:
            if tag.startswith(prefix):
                out.append(tag)
                break
    return out

# Initialize the command line interface
# These can be written into a script and run from there...
@click.group(chain=True)
@click.option('--key', required=False) # not required for read-only
@click.option('--library-id', required=True)
@click.option('--library-type', required=True,
        type=click.Choice(['user', 'group']))
@click.option('--tag-filter', default=[], multiple=True,
                help="Tag to include/exclude in queries")
@click.option('--collection-id', required=False,
                help="ID of a collection from which to create a bibliography")
@click.pass_context
def cli(ctx, key, library_id, library_type, tag_filter, collection_id):
    ctx.ensure_object(dict)
    ctx.obj['key'] = key
    ctx.obj['library_id'] = library_id
    ctx.obj['library_type'] = library_type
    ctx.obj['tag_filter'] = list(tag_filter)
    ctx.obj['collection_id'] = collection_id


@cli.command()
@click.pass_context
@click.argument('output', type=click.File("w"))
def get_tags(ctx, output):
    """Print a list of tags in the library that match the input prefix.

    Tags are filtered to include or exclude those that match the prefix strings
    given. Each match is checked at the beginning of the string (left-to-right).

    OUTPUT can be a filename or `-` to print to stdout.
    """

    zot = zotero.Zotero(ctx.obj['library_id'], ctx.obj['library_type'],
                    ctx.obj['key'])
    t = zot.everything(zot.tags(q=ctx.obj['tag_filter'], qmode='startsWith'))
    output.write('\n'.join(sorted(t)))

@cli.command()
@click.pass_context
@click.option('--print-tag', default=[], multiple=True,
                help="List of tags to include in bibliography output")
@click.argument('output', type=click.File("w"))
def print_bibliography(ctx, print_tag, output):
    """Print an html bibliography for a given collection, with tags listed
    beneath each entry.

    Tags can be filtered by providing tag prefixes through `--print-tag`.

    OUTPUT can be a filename or `-` to print to stdout.

    Example:
        python zma.py --library-type group --library-id 2183860 /
        --collection-id 27MV6NK5 print-bibliography /
        --print-tag "#THEME:" --print-tag "+" zotero.html
    """

    zot = zotero.Zotero(ctx.obj['library_id'], ctx.obj['library_type'],
                    ctx.obj['key'])
    t = zot.everything(zot.collection_items_top(ctx.obj['collection_id'],
                include='bib,data', style='mla', linkwrap='1'))
    # sort by bibliography; lowercase entries to make the sort case-insensitive
    t = sorted(t, key=lambda i: i['bib'].lower())
    for i in t:
        if print_tag:
            tags = _filter_tags([k['tag'] for k in i['data']['tags']],
                            print_tag)
        else:
            tags = i['data']['tags']
        output.write(i['bib'])
        output.write('<blockquote>')
        output.write(', '.join(tags))
        output.write('</blockquote>')

@cli.command()
@click.pass_context
@click.option('--tag', required=True, help='Tag name to apply')
@click.argument('input', type=click.File("r"))
def apply_category_tags(ctx, tag, input):
    """Apply category tags to items matching tags listed in INPUT.

    INPUT should contain a list of tags, separated by newlines. INPUT can be a
    filename or `-` to read from stdin. References matching any of the tags in
    that list will be tagged in the Zotero library with the additional tag
    specified with `--tag`. For example, INPUT could contain a list of Asian
    country names, in which case all library items tagged with one of those
    country names could additionally be given the tag "ASIA":

        python zma.py [OPTIONS] --tag ASIA asian-countries.txt
    """

    zot = zotero.Zotero(ctx.obj['library_id'], ctx.obj['library_type'],
                    ctx.obj['key'])

    subtags = input.read().splitlines()
    s = ' || '.join([t for t in subtags if t.strip() != ''])
    items = zot.everything(zot.items(tag=s))

    for item in items:
        # skip if the item already has this tag; otherwise update
        if not any(t['tag'] == tag for t in item['data']['tags']):
            click.echo('UPDATING {}'.format(item['data'].get('title')))
            zot.add_tags(item, tag)


@cli.command()
@click.pass_context
@click.option('--local', default='missing-user-tags.txt',
                help='Output for tags missing in the user-supplied file',
                show_default=True)
@click.option('--remote',
                default='missing-zotero-tags.txt',
                help='Output for tags missing in the Zotero library',
                show_default=True)
@click.argument('tags_list', type=click.File("r"))
def find_missing_tags(ctx, match, local, remote, tags_list):
    """Compare a list of tags to those in the library.

    Prints lists of tags to two plain text files, by default "missing-user-
    tags.txt" (tags that are in the Zotero library but not in the user-supplied
    file) and "missing-zotero-tags.txt" (tags that are in the user-supplied
    file but not in the Zotero library).

    This function is intended to be used where there is an established
    codebook, and you wish to check whether (1) there are any unused tags in
    the codebook, and (2) there are any tags in the Zotero library that aren't
    documented in the codebook. If the tags in the codebook have a common
    prefix, results from the Zotero library can be filtered using the `--tag-
    filter` argument.

    """

    local_tags = tags_list.read().splitlines()
    zot = zotero.Zotero(ctx.obj['library_id'], ctx.obj['library_type'],
                    ctx.obj['key'])
    remote_tags = zot.everything(zot.tags(q=ctx.obj['tag_filter'], qmode='startsWith'))

    local_only = [l for l in local_tags if not l in remote_tags]
    remote_only = [r for r in remote_tags if not r in local_tags]

    with open(remote, 'w') as out:
        out.write('\n'.join(sorted(local_only)))

    with open(local, 'w') as out:
        out.write('\n'.join(sorted(remote_only)))

@cli.command()
@click.pass_context
@click.argument('tag_x', type=click.File('r'))
@click.argument('tag_y', type=click.File('r'))
@click.argument('output', type=click.File('wb'))
def get_union(ctx, tag_x, tag_y, output):
    """Generate a CSV file containing an array of tag correlations.

    Each of TAG_X and TAG_Y is a list of tags, separated by newlines.

    Use the `--tag--filter` argument as a global filter to limit the results to
    items that match a specific tag or tags (this argument can be specified more
    than once, in which case ALL tags must be matched to be included in the
    result set). To exclude items that match a given tag, use a negative
    operator prefix (e.g., "-tag to exclude").

    Example:

        python zma.py [OPTIONS] --tag-filter="#RELEVANCE: Direct" --tag-filter \
        "-#exclude" get-union x.txt y.txt out.csv
    """

    tags_x = tag_x.read().splitlines()
    tags_y = tag_y.read().splitlines()

    fieldnames = ['tag'] + tags_x
    csvwriter = csv.DictWriter(output, fieldnames=fieldnames)
    csvwriter.writeheader()
    rows = []

    zot = zotero.Zotero(ctx.obj['library_id'], ctx.obj['library_type'],
                    ctx.obj['key'])
    for y in tags_y:
        row = {'tag': y}
        for x in tags_x:
            t = zot.everything(zot.items(tag=[x,y] + ctx.obj['tag_filter'],
                format='versions',
                limit=None))
            row[x] = len(t)
        rows.append(row)

    for row in rows:
        csvwriter.writerow(row)

@cli.command()
@click.pass_context
@click.option('--start-date', default='1900', show_default=True)
@click.option('--end-date', default='2100', show_default=True)
@click.argument('output', type=click.File('wb'))
def list_journals(ctx, start_date, end_date, output):
    """Write a table showing journal frequencies.

    Tag filters can be used to limit results. The filter argument can only be
    specified once, otherwise it will be ignored.
    """
    pubs = {}
    end = dateparse(end_date, ignoretz=True)
    start = dateparse(start_date, ignoretz=True)
    zot = zotero.Zotero(ctx.obj['library_id'], ctx.obj['library_type'],
                    ctx.obj['key'])
    items = zot.everything(zot.items(   tag=ctx.obj['tag_filter'],
                                        itemType='journalArticle'))

    for i in items:
        data = i['data']
        pub = data.get('publicationTitle', None)
        if not pub:
            continue
        pubdate = data.get('date', 'None') #use 'None' as string for error message
        try:
            date = dateparse(pubdate, fuzzy=True, ignoretz=True)
        except:
            click.echo('Unable to parse date: {}'.format(pubdate))
            continue
        if date > end or date < start:
            click.echo('Date out of range: {}'.format(pubdate))
            continue
        if not pub in pubs:
            pubs[pub] = 0
        pubs[pub] += 1

    csvwriter = csv.writer(output)
    csvwriter.writerow(['count', 'journal'])
    for (pub, count) in pubs.items():
        csvwriter.writerow([count, pub])

if __name__ == '__main__':
    cli()
