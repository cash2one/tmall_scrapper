#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Uses product and product variation details stored in database to produce new
html templates using `templates/base.html`
"""

import os
import logging

logger = logging.getLogger(__name__)

from jinja2 import Environment, FileSystemLoader
from database import *

def get_args():

    from argparse import ArgumentParser
    parser = ArgumentParser(description="TODO: description of the utility")
    parser.add_argument("-v", "--verbose", action="count", help="the logging verbosity (more gives more detail)")
    parser.add_argument("-t", "--template_dir", default="templates", help="Location of the template directory (default: %(default)s)")
    parser.add_argument("-o", "--output_dir", default="listing_html", help="Location of the output directory (default: %(default)s)")
    args = parser.parse_args()

    if args.verbose == 1:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s")
    logger.setLevel(level)

    return args


def main():
    args = get_args()
    env = Environment(loader=FileSystemLoader(args.template_dir))

    db = get_db()
    variations = db.query(Variation).filter(Variation.have_final_images==1).all()

    try:
        os.makedirs(args.output_dir)
    except:
        pass

    template = env.get_template('base.html')

    for variation in variations:

        result = template.render(variation=variation).encode( "utf-8" )
        variation.html_template=result
        db.commit()
        path = os.path.join(args.output_dir, variation.sku_internal + '.html')
        
        with open(path, "w") as of: # Produces html file in addition to storing template in db
            of.write(result)


if __name__ == '__main__':
    main()
