import sys

import click
from rich.console import Console

from pywhat import identifier, printer
from pywhat.filter import Distribution, Filter
from pywhat.helper import AvailableTags, InvalidTag, Keys, str_to_key


def print_tags(ctx, opts, value):
    if value:
        tags = sorted(AvailableTags().get_tags())
        console = Console()
        console.print("[bold #D7Afff]" + "\n".join(tags) + "[/bold #D7Afff]")
        sys.exit()


def create_filter(rarity, include, exclude):
    filters_dict = dict()
    if rarity is not None:
        rarities = rarity.split(":")
        if len(rarities) != 2:
            print("Invalid rarity range format ('min:max' expected)")
            sys.exit(1)
        try:
            if not rarities[0].isspace() and rarities[0]:
                filters_dict["MinRarity"] = float(rarities[0])
            if not rarities[1].isspace() and rarities[1]:
                filters_dict["MaxRarity"] = float(rarities[1])
        except ValueError:
            print("Invalid rarity argument (float expected)")
            sys.exit(1)
    if include is not None:
        filters_dict["Tags"] = list(map(str.strip, include.split(",")))
    if exclude is not None:
        filters_dict["ExcludeTags"] = list(map(str.strip, exclude.split(",")))

    try:
        filter = Filter(filters_dict)
    except InvalidTag:
        print(
            "Passed tags are not valid.\n"
            "You can check available tags by using: 'pywhat --tags'"
        )
        sys.exit(1)

    return filter


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.argument("text_input", required=True)
@click.option(
    "-t",
    "--tags",
    is_flag=True,
    expose_value=False,
    callback=print_tags,
    help="Show available tags and exit.",
)
@click.option(
    "-r",
    "--rarity",
    help="Filter by rarity. Rarity is how unlikely something is to be a false-positive. The higher the number, the more unlikely. This is in the range of 0:1. To filter only items past 0.5, use 0.5: with the colon on the end. Default 0.1:1",
    default="0.1:1",
)
@click.option("-i", "--include", help="Only print entries with included tags.")
@click.option("-e", "--exclude", help="Exclude tags.")
@click.option("-o", "--only-text", is_flag=True, help="Do not scan files or folders.")
@click.option("-k", "--key", help="Sort by the specified key.")
@click.option("--reverse", is_flag=True, help="Sort in reverse order.")
@click.option(
    "-br",
    "--boundaryless-rarity",
    help="Same as --rarity but for boundaryless.",
    default="0.1:1",
)
@click.option(
    "-bi", "--boundaryless-include", help="Same as --include but for boundaryless."
)
@click.option(
    "-be", "--boundaryless-exclude", help="Same as --exclude but for boundaryless."
)
def main(
    text_input,
    rarity,
    include,
    exclude,
    only_text,
    key,
    reverse,
    boundaryless_rarity,
    boundaryless_include,
    boundaryless_exclude,
):
    """
    pyWhat - Identify what something is.\n

    Made by Bee https://twitter.com/bee_sec_san\n

    https://github.com/bee-san\n

    Filtration:\n
        --rarity min:max\n
            Rarity is how unlikely something is to be a false-positive. The higher the number, the more unlikely.\n
            Only print entries with rarity in range [min,max]. min and max can be omitted.\n
            Note: PyWhat by default has a rarity of 0.1. To see all matches, with many potential false positives use `0:`.\n
        --include list\n
            Only include entries containing at least one tag in a list. List is a comma separated list.\n
        --exclude list\n
            Exclude specified tags. List is a comma separated list.\n

    Sorting:

        --key key_name

            Sort by the given key.

        --reverse

            Sort in reverse order.

        Available keys:

            name - Sort by the name of regex pattern

            rarity - Sort by rarity

            matched - Sort by a matched string

            none - No sorting is done (the default)


    Examples:

        * what 'HTB{this is a flag}'

        * what '0x52908400098527886E0F7030069857D2E4169EE7'

        * what -- '52.6169586, -1.9779857'

        * what --rarity 0.6: 'myEmail@host.org'

        * what --rarity 0: --include "credentials, username, password" --exclude "aws, credentials" 'James:SecretPassword'

    Your text must either be in quotation marks, or use the POSIX standard of "--" to mean "anything after -- is textual input".


    pyWhat can also search files or even a whole directory with recursion:

        * what 'secret.txt'

        * what 'this/is/a/path'

    """
    dist = Distribution(create_filter(rarity, include, exclude))
    boundaryless = create_filter(
        boundaryless_rarity, boundaryless_include, boundaryless_exclude
    )
    what_obj = What_Object(dist)
    if key is None:
        key = Keys.NONE
    else:
        try:
            key = str_to_key(key)
        except ValueError:
            print("Invalid key")
            sys.exit(1)
    identified_output = what_obj.what_is_this(
        text_input, only_text, key, reverse, boundaryless
    )

    p = printer.Printing()
    p.pretty_print(identified_output, text_input)


class What_Object:
    def __init__(self, distribution):
        self.id = identifier.Identifier(dist=distribution)

    def what_is_this(
        self, text: str, only_text: bool, key, reverse: bool, boundaryless: Filter
    ) -> dict:
        """
        Returns a Python dictionary of everything that has been identified
        """
        return self.id.identify(
            text,
            only_text=only_text,
            key=key,
            reverse=reverse,
            boundaryless=boundaryless,
        )


if __name__ == "__main__":
    main()
