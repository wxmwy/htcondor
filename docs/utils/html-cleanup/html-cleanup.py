#!/usr/bin/env python

import bs4
import os
import re
import sys

from url_data import *



def dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))


# Cleans up the <br/> and newline formatting inside a list of markup elements
def cleanup_pre_contents(data):
    # First, rip out all the newlines
    for index, token in enumerate(data):
        if token:
            utf8_token = token.encode("utf-8")
            if utf8_token == "\n":
                data.remove(token)
    # Next, add a newline bs4.element.NavigableString after every <br/> tag
    for index, token in enumerate(data):
        if token:
            utf8_token = token.encode("utf-8")
            if "<br/>" in utf8_token:
                newline_tag = bs4.element.NavigableString("\n")
                data.insert(index + 1, newline_tag)
    return data


# Cleans up the markup of a table
def cleanup_table(data):
    # First, determine how many columns this table has.
    num_columns = 0
    for index, token in enumerate(data):
        if token.name == "tr":
            this_row_columns = len(list(token.children))
            if this_row_columns > num_columns:
                num_columns = this_row_columns
    # Now determine which elements we want to remove from the table.
    # Do not remove them now, that causes the iterator to miss elements.
    # Instead flag them for removal later.
    tokens_to_remove = []
    for index, token in enumerate(data):
        if type(token) is bs4.element.Tag:
            #print("\n\ntoken name = " + str(token.name) + ", # children = " + str(len(list(token.children))))
            #print("token = " + str(token))
            # Remove all the <tr class="hline">...</tr> tags
            if token.name == "tr" and "class" in token.attrs.keys():
                tokens_to_remove.append(token)
                #print("Marking index " + str(index) + " for removal")
            elif token.name == "colgroup":
                tokens_to_remove.append(token)
                #print("Marking index " + str(index) + " for removal")
            elif len(list(token.children)) != num_columns:
                tokens_to_remove.append(token)
                #print("Marking index " + str(index) + " for removal")
    # Now, finally, remove all the bad elements.
    for index, token in enumerate(tokens_to_remove):
        data.remove(token)
    return data

# Updates a link URL and also adds in the correct title
def update_link(data):
    updated_link = data
    # Try updating the link. If the link is external, the following block will fail and the link will remain as-is.
    try:
        # Determine what page this is linking to
        old_url = data['href'].split("#")[0]
        updated_link['href'] = updated_urls[old_url]
        updated_link.string = updated_titles[old_url]
    except:
        print("Link " + str(data) + " is external, ignoring")
    return updated_link



def main():

    # Command line arguments
    if len(sys.argv) < 2:
        print("Usage: html-cleanup.py <input-file> [Optional]: <output-file>")
        sys.exit(1)
    
    # Open the input file
    input_filename = str(sys.argv[1])
    with open(input_filename, "r") as input_file:
        html_data = input_file.read()
    input_file.close()

    # Check if output file was specified, if so record it
    output_filename = input_filename + ".out"
    if len(sys.argv) >= 3:
        output_filename = str(sys.argv[2])

    # Now start The Great HTML Parse!
    print("Cleaning up " + input_filename + " to " + output_filename)
    soup = bs4.BeautifulSoup(html_data, features="lxml")

    # STEP 1
    # Delete things we don't want. Do this before editing any markup.

    # Delete the navigation tags (defined by <span style="font-size: 200%;>...</span>")
    nav_tags = soup.find_all("span", attrs={"style": "font-size: 200%;"})
    #print("Found " + str(len(nav_tags)) + " navigation spans")
    for tag in nav_tags:
        tag.decompose()

    # Delete the "Contents" and "Index" links. Also delete all empty links.
    # Wait, we can use the empty links to identify indexes. Keep them for now.
    links_tags = soup.find_all("a")
    for tag in links_tags:
        if tag.string:
            if tag.string == "Contents" or tag.string == "Index":
                tag.decompose()
        #else:
        #    # We don't want to delete links that have an href set
        #    if "href" not in tag.attrs:
        #        tag.decompose()

    # Delete the table of contents
    toc_tags = soup.find_all("div", attrs={"class": "sectionTOCS"})
    for tag in toc_tags:
        tag.decompose()

    # Delete the section numbering
    titlemark_tags = soup.find_all("span", attrs={"class": "titlemark"})
    for tag in titlemark_tags:
        tag.decompose()

    # Delete all hidden spans
    hidden_span_tags = soup.find_all("span", attrs={"style": "visibility: hidden;"})
    print("Found " + str(len(hidden_span_tags)) + " hidden spans")
    for tag in hidden_span_tags:
        tag.decompose()

    # At this point, soup is sufficiently confused that we should reload the contents of our HTML markup
    html_dump = str(soup)
    soup = bs4.BeautifulSoup(html_dump, features="lxml")

    # STEP 2
    # Now manipulate the elements we want to keep

    # Convert all <span class="textbf">...</span> tags to <b>...</b>
    bold_tags = soup.find_all("span", attrs={"class": "textbf"})
    print("Found " + str(len(bold_tags)) + " textbf spans")
    for tag in bold_tags:
        new_tag = soup.new_tag("b")
        if tag.string:
            new_tag.string = tag.string
        tag.replace_with(new_tag)

    # Convert all <span class="textit">...</span> tags to <i>...</i>
    italic_tags = soup.find_all("span", attrs={"class": "textit"})
    print("Found " + str(len(italic_tags)) + " textit spans")
    for tag in italic_tags:
        new_tag = soup.new_tag("i")
        if tag.string:
            new_tag.string = tag.string
        #print("new_tag = " + str(new_tag))
        #print("new_tag.parent" + str(new_tag.parent))
        tag.replace_with(new_tag)

    # Convert all <br class="newline" /> tags to <br />
    br_newline_tags = soup.find_all("br", attrs={"class": "newline"})
    print("Found " + str(len(br_newline_tags)) + " br newline tags")
    for tag in br_newline_tags:
        new_tag = soup.new_tag("br")
        tag.replace_with(new_tag)

    # Convert all <h3> tags to <h1>
    h3_tags = soup.find_all("h3")
    print("Found " + str(len(h3_tags)) + " h3 tags")
    for tag in h3_tags:
        #print("tag = " + str(tag))
        new_tag = soup.new_tag("h1")
        if tag.string:
            #print("tag.string = " + tag.string)
            new_tag.string = tag.string
        else:
            if tag.contents:
                #print("tag.contents = " + str(tag.contents))
                new_tag.contents = tag.contents
        tag.replace_with(new_tag)

    # Soup is confused. Reload.
    html_dump = str(soup)
    soup = bs4.BeautifulSoup(html_dump, features="lxml")

    # Convert all <h4> tags to <h2>
    h4_tags = soup.find_all("h4")
    print("Found " + str(len(h4_tags)) + " h4 tags")
    for tag in h4_tags:
        new_tag = soup.new_tag("h2")
        if tag.string:
            new_tag.string = tag.string
        else:
            if tag.contents:
                new_tag.contents = tag.contents
        tag.replace_with(new_tag)

    # Convert all <h5> tags to <h3>
    h5_tags = soup.find_all("h5")
    print("Found " + str(len(h5_tags)) + " h5 tags")
    for tag in h5_tags:
        new_tag = soup.new_tag("h3")
        if tag.string:
            new_tag.string = tag.string
        else:
            if tag.contents:
                new_tag.contents = tag.contents
        tag.replace_with(new_tag)

    # Soup is confused. Reload.
    html_dump = str(soup)
    soup = bs4.BeautifulSoup(html_dump, features="lxml")

    # Convert all <div class="verbatim">...</div> tags to <pre>...</pre>
    pre_tags = soup.find_all("div", attrs={"class": "verbatim"})
    print("Found " + str(len(pre_tags)) + " verbatim divs")
    for tag in pre_tags:
        new_tag = soup.new_tag("pre")
        new_tag.contents = cleanup_pre_contents(tag.contents)
        tag.replace_with(new_tag)

    # Soup is confused. Reload.
    html_dump = str(soup)
    soup = bs4.BeautifulSoup(html_dump, features="lxml")

    # Convert all <code>...</code> tags to <pre>...</pre>
    code_tags = soup.find_all("code")
    print("Found " + str(len(code_tags)) + " code divs")
    for tag in code_tags:
        new_tag = soup.new_tag("pre")
        new_tag.contents = cleanup_pre_contents(tag.contents)
        tag.replace_with(new_tag)

    # Convert all <span class="texttt">...</span> tags to <code>...</code>.
    # This needs to happen after converting all <code> tags to <pre>
    spantt_tags = soup.find_all("span", attrs={"class": "texttt"})
    print("Found " + str(len(spantt_tags)) + " texttt spans")
    for tag in spantt_tags:
        new_tag = soup.new_tag("code")
        if tag.string:
            new_tag.string = tag.string
        else:
            if tag.contents:
                new_tag.contents = tag.contents
        tag.replace_with(new_tag)

    # Cleanup table formatting so that pandoc knows what to do with them
    table_tags = soup.find_all("table")
    print("Found " + str(len(table_tags)) + " table tags")
    for tag in table_tags:
        new_tag = soup.new_tag("table")
        new_tag.contents = cleanup_table(tag.contents)
        tag.replace_with(new_tag)

    # Update links to point to correct URLs
    a_tags = soup.find_all("a")
    print("Found " + str(len(a_tags)) + " a tags")
    for tag in a_tags:
        if "href" in tag.attrs.keys():
            updated_link = update_link(tag)
            tag.replace_with(updated_link)

    # Soup is confused. Reload.
    html_dump = str(soup)
    soup = bs4.BeautifulSoup(html_dump, features="lxml")

    # Update images to point to correct src files
    # .... not worth it. We only have ~10 images in strange formats. Do it manually.

    # Is there anything we can do to automate the index items?
    # .... maybe by looking at the <a id="...">...</a> tags generated from the \Macro tags?
    index_tags = soup.find_all("a")
    print("Found " + str(len(index_tags)) + " a tags which may or may not be index items")
    for tag in index_tags:
        if "id" in tag.attrs.keys():
            new_tag = soup.new_tag("div")
            #new_tag.string = "INDEX GOES HERE"
            #tag.replace_with(new_tag)
            


    # Does outputting pretty HTML matter? 
    # Actually we do NOT want pretty HTML, since this introduces spacing that confuses pandoc.
    #pretty_html = soup.prettify().encode('utf-8')
    #print(str(pretty_html))
    output_html = str(soup)

    # Overwrite the original file with the parseable markup
    output_file = open(output_filename, "w")
    output_file.write(output_html)
    output_file.close()

if __name__ == "__main__":
    main()
