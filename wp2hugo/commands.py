"""A Python CLI application that converts a WordPress WXR backup
 file to MD files usable by Hugo.
 """

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import click
from markdownify import markdownify

NAMESPACES = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


@click.command()
@click.argument("xmlfile", type=click.File("r"), required=True)
@click.argument("outdir", default="./out", type=click.Path())
@click.option(
    "-l",
    "--lowercasetags",
    is_flag=True,
    help="Use lower case tags from export?",
    default=False,
    show_default=True,
)
def create(xmlfile, outdir, lowercasetags):
    """Opens the WXR XML and creates exported MD files

    Parameters
    ----------
    xmlfile : path
        The path to the XML file to parse
    outdir : path
        The path where the created MD files will be stored
    lowercasetags : bool
        Whether or not to lowercase the tags found in the XML file
    """

    blog = Blog.from_file(xmlfile, lowercasetags)

    out_dir = Path(outdir)
    out_dir = out_dir / blog.title

    posts_dir = out_dir / "posts"
    posts_dir.mkdir(exist_ok=True, parents=True)

    drafts_dir = out_dir / "drafts"
    drafts_dir.mkdir(exist_ok=True, parents=True)

    for post in blog.posts:
        if post.is_draft:
            file = drafts_dir / f"{post.id}.md"
        else:
            file = posts_dir / f"{post.date.date()}-{post.name}.md"

        file.write_text(post.to_md())


@click.command()
@click.argument("xmlfile", type=click.File("r"), required=1)
@click.option(
    "-l",
    "--lowercasetags",
    is_flag=True,
    help="Use lower case tags from export?",
    default=False,
    show_default=True,
)
def stats(xmlfile, lowercasetags):
    """Opens the WXR XML and dumps some statistics

    Parameters
    ----------
    xmlfile : path
        The path to the XML file to parse
    lowercasetags : bool
        Whether or not to lowercase the tags found in the XML file
    """

    blog_info = Blog.from_file(xmlfile, lowercasetags)

    click.echo(f"Title: {blog_info.title}")
    click.echo(f"Description: {blog_info.description}")
    click.echo(f"URL: {blog_info.url}")
    click.echo(f"Number of posts found: {blog_info.number_of_posts}")
    click.echo(f"Number of pages found: {blog_info.number_of_pages}")
    click.echo(f"Number of tags found: {blog_info.number_of_tags}")
    click.echo(f"Number of categories found: {blog_info.number_of_categories}")


def get_display_name_by_login(author_login, xml_data):
    """Returns the name of the author based on the author login string

    Parameters
    ----------
    author_login : str
        The author login name as found when parsing post object
    xml_data : str
        The XML data with all the authors found in the WXR file

    Returns
    -------
    str
        The name of the author if found, None if not found
    """

    root = ET.fromstring(xml_data)
    xpath_expression = (
        f".//wp:author[wp:author_login='{author_login}']/wp:author_display_name"
    )
    display_name_element = root.find(xpath_expression, NAMESPACES)

    if display_name_element is not None:
        return display_name_element.text
    return None


def make_safe_yaml_value(input_string):
    """Returns a properly quoted YAML string

    Parameters
    ----------
    input_string : str
        A string of text that needs to be YAML qouted

    Returns
    -------
    str
        Returns a properly quoted YAML string
    """

    # Check if quoting is necessary
    if any(char in input_string for char in ":{}[],*&!%@"):
        # Use double quotes if the string contains single quotes
        if "'" in input_string:
            return f'"{input_string}"'
        return f"'{input_string}'"
    return input_string


@dataclass
class Blog:
    """Represents a WordPress blog object

    Attributes:
        title : str
            The title as defined by the <title> in the WXR file
        description : str
            The description as defined by the <description> in the WXR file
        url : str
            The URL to the WordPress site as defined in the WXR file
        number_of_posts : int
            Number of posts found in the WXR file
        number_of_pages : int
            Number of pages found in the WXR file
        number_of_tags : int
            Number of tags found in the WXR file
        number_of_categories : int
            Number of categories found in the WXR file
        posts : list
            A list object with all the posts found in the WXR file
    """

    title: str
    description: str
    url: str
    number_of_posts: int
    number_of_pages: int
    number_of_tags: int
    number_of_categories: int
    posts: list

    @classmethod
    def from_file(cls, input_file: Path, lowercasetags):
        """Create a Blog object from a WXR file"""
        tree = ET.parse(input_file)

        # The root of WXR is an <rss> element, followed by a <channel> element
        channel = tree.getroot().find("channel")

        title = channel.find("title").text
        description = channel.find("description").text
        url = channel.find("link").text

        tmp_authors = channel.findall("wp:author", NAMESPACES)
        merged_root = ET.Element("root")
        for element in tmp_authors:
            merged_root.append(element)

        # merged_tree = ET.ElementTree(merged_root)
        merged_xml_string = ET.tostring(merged_root, encoding="utf-8").decode("utf-8")
        authors = merged_xml_string

        number_of_posts = len(
            channel.findall(".//item[wp:post_type='post']", NAMESPACES)
        )
        number_of_pages = len(
            channel.findall(".//item[wp:post_type='page']", NAMESPACES)
        )
        number_of_tags = len(channel.findall(".//wp:tag", NAMESPACES))
        number_of_categories = len(channel.findall(".//wp:category", NAMESPACES))

        posts = [
            Post.from_element(e, lowercasetags, authors)
            for e in channel.findall("item")
            if e.find("wp:post_type", NAMESPACES).text in ["post", "page"]
        ]

        return cls(
            title=title,
            description=description,
            url=url,
            posts=posts,
            number_of_posts=number_of_posts,
            number_of_pages=number_of_pages,
            number_of_tags=number_of_tags,
            number_of_categories=number_of_categories,
        )


@dataclass
class Post:
    """Represents a WordPress blog post

    Attributes
    ----------
        id : int
            ID of the post
        title : str
            Title of the post
        name : str
            Name of the post
        author : str
            Name of the author for the post
        content : str
            The actual content of the post
        date : datetime
            When the post was published
        datestr : str
            When the post was published, string with quotes
        modified : datetime
            When the post was last modified
        modifiedstr : str
            When the post was last modified, string with quotes
        categories : string
            A string list of the categories linked with the post
        tags : str
            A string list of the tags linked with the post
        post_type : str
            What sort of post it is
        is_draft : bool
            Whether or not the post is a draft or not
    """

    id: int
    title: str
    name: str
    author: str
    content: str
    date: datetime
    datestr: str
    modified: datetime
    modifiedstr: str
    categories: str
    tags: str
    post_type: str
    is_draft: bool

    DATE_IN_BODY_FORMAT = "%a %d %b %Y, %I:%M"

    @classmethod
    def from_element(cls, element: ET.Element, use_tag_nicename, authors):
        """Create a post from an XML element"""
        title = element.find("title").text
        title = make_safe_yaml_value(title)

        name = element.find("wp:post_name", NAMESPACES).text
        creator = element.find("dc:creator", NAMESPACES).text
        author = get_display_name_by_login(creator, authors)

        post_id = element.find("wp:post_id", NAMESPACES).text
        content = element.find("content:encoded", NAMESPACES).text
        if content is not None:
            content = markdownify(content)
            content = re.sub(r"\n\s*\n", "\n\n", content)
        try:
            date = datetime.fromisoformat(element.find("wp:post_date", NAMESPACES).text)
            datestr = f'"{date}"'
        except ValueError:
            date = None

        try:
            modified = datetime.fromisoformat(
                element.find("wp:post_modified", NAMESPACES).text
            )
            modifiedstr = f'"{modified}"'
        except ValueError:
            modified = None

        categories = [e.text for e in element.findall("category[@domain='category']")]
        categories = "\n".join("  -" + " " + x for x in categories)

        if use_tag_nicename:
            tags = [
                e.get("nicename")
                for e in element.findall("category[@domain='post_tag']")
            ]
            tags = "\n".join("  -" + " " + x for x in tags)
        else:
            tags = [e.text for e in element.findall("category[@domain='post_tag']")]
            tags = "\n".join("  -" + " " + x for x in tags)

        post_type = element.find("wp:post_type", NAMESPACES).text

        is_draft = element.find("wp:status", NAMESPACES).text == "draft"

        return cls(
            title=title,
            name=name,
            author=author,
            id=post_id,
            content=content,
            date=date,
            datestr=datestr,
            modified=modified,
            modifiedstr=modifiedstr,
            categories=categories,
            tags=tags,
            post_type=post_type,
            is_draft=is_draft,
        )

    def md_frontmatter(self) -> str:
        """Generate YAML metadata lines to be included in the markdown string"""

        lines = []
        lines.append("---")
        lines.append(f"id: {self.id}")
        lines.append("layout: post")
        lines.append(f"title: {self.title}")
        lines.append(f"author: {self.author}")
        lines.append(f"date: {self.datestr}")
        lines.append(f"modified: {self.modifiedstr}")
        if len(self.categories) > 0:
            lines.append(f"categories:\n{self.categories}")
        if len(self.tags) > 0:
            lines.append(f"tags:\n{self.tags}")
        if self.is_draft:
            lines.append("draft: true")
        lines.append("---")
        lines.append("")
        return "\n".join(lines)

    def md_body(self, include_title=False, include_date=False) -> str:
        """Generate markdown text body lines"""
        lines = []
        if self.title is not None and include_title:
            lines.append(f"# {self.title}")
            lines.append("")
        if self.date is not None and include_date:
            lines.append(f"_{self.date.strftime(self.DATE_IN_BODY_FORMAT)}_")
            lines.append("")
        if self.content is not None:
            lines.append(f"{self.content}")
            lines.append("")
        return "\n".join(lines)

    def to_md(self) -> str:
        """Convert post into a markdown string"""
        md = ""
        md += self.md_frontmatter()
        md += self.md_body()
        return md
