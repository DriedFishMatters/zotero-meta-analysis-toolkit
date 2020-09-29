# zotero-meta-analysis-toolkit

Command-line tools to support meta-analysis using a library managed in Zotero

This command-line tool operates on a Zotero database, using the `pyzotero` API,
to obtain basic quantitative measures about the distribution of references
according to user-applied thematic tags. While not optimized for speed or
efficiency, this script is relatively easy to adapt as it makes use of the
convenient tag-filtering and other queries that are built into the Zotero API,
which avoids needing to parse the complex data structure in a Zotero RDF or json
dump.

The tool assumes a workflow in which significant metadata concerning each item
are encoded in Zotero tags. The primary output of query operations will be a CSV
file containing a two-dimensional tags array, displaying the count of articles
matching both tags for each cell in the array. For example, it would be possible
to query a Zotero library by geographic region and by theme, to generate tabular
output like the following:

  tag      | Culture  | History
  -------- | -------- | --------        
  Asia     | 27       | 96
  Europe   | 18       | 40

Each axis in the sample array above is constructed from a list of tags supplied
to the `get_union` command.

## Usage

  ```
  $ zma.py [OPTIONS] COMMAND [ARGS]...
  ```

## Global options

### `--key TEXT`

(Required)

The API key for your Zotero user or group library. This will be a seven-digit
code available from the settings page at <https://www.zotero.org/settings/keys>.

### `--library-id TEXT`

(Required)

For a personal library, the library ID is listed on the "keys" page (see above)
as "Your userID for use in API calls". For a group library, the ID will be part
of the group URL -- for example, for the group
<http://zotero.org/groups/2183860/dried_fish_matters/> the library ID is
`2183860`.

### `--library-type [user|group]`

(Required)

Indicate whether the Zotero library you are accessing is owned by a user or a
group.

### `--tag-filter TEXT`

Tag to include/exclude in query commands. The `TEXT` string will match anywhere
at the beginning of a tag, so `--tag-filter theme_` would match the tags
`theme_culture` and `theme_history`.

This option can generally be specified more than once, in which case it will
serve as a logical AND by returning tags that match all of the strings given.

Tags can be excluded by prefixing the string with a minus, sign (e.g.,
`--tag-filter -exclude` will limit the results to items that do not have the tag
"exclude").

A logical OR is represented as "||" (e.g., `--tag-filter "foo || bar"` will
return items that have tags beginning with either "foo" or "bar").

## Commands

### `get_tags`

Usage:

```
  python zma.py [OPTIONS] get_tags OUTPUT
```

Print a list of tags in the library.

Tags are filtered to include or exclude those that match the prefix strings
given with `--tag-filter`; otherwise all tags are returned.

`OUTPUT` can be a filename or `-` to print to stdout.


### `apply_category_tags`

Usage:

```
   python zma.py [OPTIONS] apply_category_tags --tag TEXT INPUT
```

Apply category tags to items matching tags listed in `INPUT`.

`INPUT` should contain a list of tags, separated by newlines. `INPUT` can be a
filename or `-` to read from stdin. References matching any of the tags in
that list will be tagged in the Zotero library with the additional tag
specified with `--tag`. For example, `INPUT` could contain a list of Asian
country names, in which case all library items tagged with one of those
country names could additionally be given the tag "ASIA":

```
  python zma.py [OPTIONS] apply_category_tags --tag ASIA asian-countries.txt
```

### `find_missing_tags`

Usage:

```
  zma.py [OPTIONS] find_missing_tags [--local FILE] [--remote FILE] TAGS_LIST
```

Compare a list of tags to those in the library.

Prints missing tags to two plain text files, by default "missing-local.txt" and
"missing-remote.txt". The names of the output files can be set using the options
`--local` (list of tags missing in the local tag list) and `--remote` (list of
tags missing in the remote Zotero library).

`TAGS_LIST` is the name of a plain-text file or stream containing a list of
files to check, one per line. Use the `get_tags` command to generate a baseline
list as needed.


### `get_union`

Usage:

```
  zma.py [OTPIONS] graph TAG_X TAG_Y OUTPUT
```

Generate a CSV file containing an array of tag correlations.

Each of `TAG_X` and `TAG_Y` is a plain-text file or stream containing a list of tags, separated by newlines.

Use the `--tag--filter` argument as a global filter to limit the results to
items that match a specific tag or tags (this argument can be specified more
than once, in which case ALL tags must be matched to be included in the
result set).

Example:

```
  zma.py [OPTIONS] --tag-filter="#RELEVANCE: Direct" --tag-filter \
    "-#exclude" get_union x.txt y.txt out.csv
```

### `graph`

Usage:

```
  zma.py [OPTIONS] graph INPUT OUTPUT
```

Generate a graph from a CSV file (or stream via stdin) provided as `INPUT` and
write the image to `OUTPUT`.

This function, which uses Pandas to create a simple horizontal bar graph, is
mainly intended for use in piping output from a `get_union` query. More advanced
analyses and visualizations can be constructed using Pandas directly. `OUTPUT`
can be the filename for an image (e.g., `output.png`) or document (e.g.,
`output.pdf`); the filename will control the nature of the output.

### `list_journals`

Usage:

```
  zma.py [OPTIONS] list_journals [--start-date DATE] [--end-date DATE] OUTPUT
```

Write a table showing journal frequencies. `OUTPUT` will be a CSV file
containing two columns: the ranked number of occurrences in the library of
articles in each journal, and the name of each journal.

Tag filters can be used to limit results. Note that the `--tag-filter` argument
can only be specified once for this command, otherwise it will be ignored.

The `--start-date` (default: 1900) and `--end-date` (default: 2100) options may
be used to limit output to a specific temporal range. Most date strings can be
parsed successfully, although a four-digit year as input will be least
ambiguous.

## Copying

Copyright 2020, Eric Thrift

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

## Credits

This script was originally written for the 
[Dried Fish Matters](https://driedfishmatters.org) project, supported 
by the [Social Sciences and Humanities Research Council of 
Canada](http://sshrc-crsh.gc.ca).
